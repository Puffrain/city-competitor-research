#!/usr/bin/env python3
"""Shared Amap helpers. Never print the API key."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path


def load_key(env_file: str | None = None) -> str:
    key = (os.environ.get("AMAP_MAPS_API_KEY") or "").strip()
    candidates = []
    if env_file:
        candidates.append(Path(env_file))
    cwd = Path.cwd()
    candidates.extend([cwd / "secrets" / "amap.env", cwd / "amap.env"])
    for path in candidates:
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("AMAP_MAPS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if key:
            break
    if not key:
        raise SystemExit(
            "缺少高德 Web 服务 Key。请设置 AMAP_MAPS_API_KEY，或写到 secrets/amap.env。"
        )
    return key


def get_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def amap_get(path: str, key: str, **params) -> dict:
    params = {k: v for k, v in params.items() if v not in (None, "")}
    params["key"] = key
    url = f"https://restapi.amap.com{path}?" + urllib.parse.urlencode(params)
    data = get_json(url)
    if str(data.get("status")) != "1":
        info = data.get("info") or data.get("infocode") or "unknown"
        raise RuntimeError(f"高德接口失败 {path}: {info}")
    return data


def norm_text(v) -> str:
    if v is None or v in ([], "", "[]"):
        return ""
    if isinstance(v, list):
        return "".join(str(x) for x in v if x not in ([], None))
    return str(v)


def norm_tel(v) -> str:
    if not v or v in ([], "", "[]"):
        return ""
    if isinstance(v, list):
        return ";".join(str(x) for x in v if x)
    return str(v)


def parse_location(loc: str) -> tuple[float | None, float | None]:
    loc = norm_text(loc)
    if "," not in loc:
        return None, None
    lon, lat = loc.split(",", 1)
    try:
        return float(lon), float(lat)
    except ValueError:
        return None, None


def sleep_politely(seconds: float = 0.12) -> None:
    time.sleep(seconds)
