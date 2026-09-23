#!/usr/bin/env python3
"""Search operating competitors in one city via Amap place APIs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from amap_common import amap_get, load_key, norm_tel, norm_text, parse_location, sleep_politely

DEFAULT_EXCLUDE = [
    r"打印店|图文店|复印",
    r"会计|考证|驾校|考研|雅思|托福",
    r"餐饮|火锅|烧烤|奶茶|咖啡",
    r"公寓|民宿|酒店|旅馆",
    r"泡泡玛特|盲盒",
    r"房产|中介",
]


def split_csv(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def poi_record(p: dict, keyword: str) -> dict:
    lon, lat = parse_location(p.get("location"))
    biz = p.get("biz_ext") or {}
    return {
        "id": norm_text(p.get("id")),
        "name": norm_text(p.get("name")),
        "type": norm_text(p.get("type")),
        "typecode": norm_text(p.get("typecode")),
        "address": norm_text(p.get("address")),
        "adname": norm_text(p.get("adname")),
        "pname": norm_text(p.get("pname")),
        "cityname": norm_text(p.get("cityname")),
        "tel": norm_tel(p.get("tel")),
        "location": norm_text(p.get("location")),
        "lon": lon,
        "lat": lat,
        "business_area": norm_text(p.get("business_area")),
        "rating": norm_text(biz.get("rating")),
        "cost": norm_text(biz.get("cost")),
        "opentime": norm_text(biz.get("open_time") or biz.get("opentime2")),
        "alias": norm_text(p.get("alias")),
        "atag": norm_text(p.get("atag") or p.get("tag")),
        "website": norm_text(p.get("website")),
        "keywords": [keyword] if keyword else [],
    }


def merge_poi(seen: dict, p: dict, keyword: str) -> None:
    rec = poi_record(p, keyword)
    pid = rec["id"] or f"{rec['name']}|{rec['location']}"
    cur = seen.setdefault(pid, rec)
    if keyword and keyword not in cur["keywords"]:
        cur["keywords"].append(keyword)
    for k in ("tel", "rating", "cost", "opentime", "website", "alias", "atag", "business_area"):
        if not cur.get(k) and rec.get(k):
            cur[k] = rec[k]
    if cur.get("lon") is None:
        cur["lon"], cur["lat"] = rec["lon"], rec["lat"]


def excluded(name: str, typ: str, patterns: list[str]) -> str | None:
    text = f"{name} {typ}"
    for pat in patterns:
        if re.search(pat, text, re.I):
            return pat
    return None


def search_keyword(key: str, city: str, keyword: str, pages: int) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        data = amap_get(
            "/v3/place/text",
            key,
            keywords=keyword,
            city=city,
            citylimit="true",
            offset="25",
            page=str(page),
            extensions="all",
        )
        pois = data.get("pois") or []
        out.extend(pois)
        count = int(data.get("count") or 0)
        if page * 25 >= min(count, pages * 25) or len(pois) < 25:
            break
        sleep_politely(0.12)
    return out


def district_list(key: str, city: str) -> tuple[dict, list[str]]:
    data = amap_get(
        "/v3/config/district",
        key,
        keywords=city,
        subdistrict="1",
        extensions="base",
    )
    districts = data.get("districts") or []
    if not districts:
        raise RuntimeError(f"找不到城市：{city}")
    root = districts[0]
    children = [norm_text(x.get("name")) for x in (root.get("districts") or []) if x.get("name")]
    return root, children


def simplify_ring(pts: list[list[float]], eps: float = 0.00035) -> list[list[float]]:
    if len(pts) < 8:
        return pts

    def dist(p, a, b):
        y, x = p
        y1, x1 = a
        y2, x2 = b
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        return ((x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2) ** 0.5

    def rdp(seq):
        if len(seq) < 3:
            return seq
        dmax, idx = 0.0, 0
        for i in range(1, len(seq) - 1):
            d = dist(seq[i], seq[0], seq[-1])
            if d > dmax:
                idx, dmax = i, d
        if dmax > eps:
            return rdp(seq[: idx + 1])[:-1] + rdp(seq[idx:])
        return [seq[0], seq[-1]]

    out = rdp(pts)
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def city_boundary(key: str, city: str) -> dict:
    data = amap_get(
        "/v3/config/district",
        key,
        keywords=city,
        subdistrict="0",
        extensions="all",
    )
    d = (data.get("districts") or [None])[0]
    if not d:
        raise RuntimeError(f"找不到边界：{city}")
    poly = d.get("polyline") or ""
    rings = []
    for ring in str(poly).split("|"):
        pts = []
        for part in ring.split(";"):
            if not part or "," not in part:
                continue
            lon, lat = part.split(",", 1)
            pts.append([float(lat), float(lon)])
        if len(pts) >= 4:
            rings.append(simplify_ring(pts))
    if not rings:
        raise RuntimeError(f"{city} 没有行政区边界")
    main = max(rings, key=len)
    center = norm_text(d.get("center"))
    lon, lat = parse_location(center)
    return {
        "name": norm_text(d.get("name")),
        "adcode": norm_text(d.get("adcode")),
        "level": norm_text(d.get("level")),
        "center": {"lon": lon, "lat": lat},
        "rings": [main],
    }


def guess_brand(name: str) -> str:
    n = re.sub(r"（.*?）|\(.*?\)", "", name).strip()
    n = re.split(r"店|校区|中心|创意中心|体验中心", n)[0].strip(" ·-")
    return n or name


def classify_priority(name: str, typ: str, keywords: list[str], industry: str) -> tuple[str, str]:
    text = f"{name} {typ} {' '.join(keywords)} {industry}"
    adjacent = bool(re.search(r"学科|学习机|智适应|智学|一对一|课外辅导|春华|昂立|学而思", text, re.I))
    core = bool(re.search(r"编程|机器人|乐高|创客|STEAM|steam|科创|3D|人工智能|AI", text, re.I))
    if adjacent and not core:
        return "相邻", "P3 相邻入口"
    if core:
        known = bool(re.search(r"斯坦星球|乐博乐博|凤凰机器人|能力风暴|童程|核桃|编程猫|小码王|西瓜创客|贝尔|乐高", name, re.I))
        return "核心", "P1 优先深挖" if known else "P2 核心补全"
    return "待核", "P2 核心补全"


def main() -> None:
    ap = argparse.ArgumentParser(description="按城市和行业检索高德竞品")
    ap.add_argument("--city", required=True)
    ap.add_argument("--industry", default="少儿编程,机器人教育")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--expand-districts", action="store_true")
    ap.add_argument("--exclude", default=",".join(DEFAULT_EXCLUDE))
    ap.add_argument("--env-file", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    key = load_key(args.env_file or None)
    keywords = split_csv(args.keywords) or split_csv(args.industry)
    exclude_pats = split_csv(args.exclude)
    root, children = district_list(key, args.city)
    city_name = norm_text(root.get("name")) or args.city
    bound = city_boundary(key, args.city)

    seen: dict[str, dict] = {}
    errors = []
    kw_counts = Counter()
    queries = [(None, kw) for kw in keywords]
    if args.expand_districts:
        for district in children:
            for kw in keywords:
                queries.append((district, kw))

    for district, kw in queries:
        q = kw if not district else f"{district} {kw}"
        try:
            pois = search_keyword(key, args.city, q, 2 if district else args.pages)
        except Exception as e:
            errors.append({"district": district, "keyword": kw, "error": str(e)})
            sleep_politely(0.6)
            continue
        kw_counts[kw] += len(pois)
        for p in pois:
            merge_poi(seen, p, kw)
        print(f"{city_name} {district or '-'} {kw}: hits={len(pois)} unique={len(seen)}", flush=True)
        sleep_politely(0.1)

    items = []
    dropped = []
    for rec in seen.values():
        why = excluded(rec["name"], rec["type"], exclude_pats)
        if why:
            dropped.append({"name": rec["name"], "reason": why})
            continue
        relevance, priority = classify_priority(rec["name"], rec["type"], rec["keywords"], args.industry)
        rec["brand"] = guess_brand(rec["name"])
        rec["relevance"] = relevance
        rec["priority"] = priority
        rec["status"] = "在营"
        rec["amap"] = f"https://www.amap.com/place/{rec['id']}" if rec.get("id") else ""
        items.append(rec)

    items.sort(key=lambda x: ({"P1 优先深挖": 0, "P2 核心补全": 1, "P3 相邻入口": 2}.get(x["priority"], 9), x["name"]))
    for i, rec in enumerate(items, 1):
        rec["no"] = i
        rec["lab"] = rec["brand"][:12] or rec["name"][:12]

    payload = {
        "city": args.city,
        "city_name": city_name,
        "industry": args.industry,
        "keywords": keywords,
        "keyword_counts": dict(kw_counts),
        "districts": children,
        "boundary": bound,
        "total_raw": len(seen),
        "total_kept": len(items),
        "dropped": dropped,
        "errors": errors,
        "items": items,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SAVED {out} kept={len(items)} dropped={len(dropped)} errors={len(errors)}", flush=True)


if __name__ == "__main__":
    main()
