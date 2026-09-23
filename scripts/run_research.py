#!/usr/bin/env python3
"""Run the city competitor workflow: search -> Word report -> Amap HTML map."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    ap = argparse.ArgumentParser(description="行业 + 城市 -> 竞品报告和地图")
    ap.add_argument("--city", required=True)
    ap.add_argument("--industry", required=True, help="行业名，或逗号分隔关键词")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--expand-districts", action="store_true")
    ap.add_argument("--env-file", default="")
    ap.add_argument("--exclude", default="")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{args.city}{args.industry.split(',')[0]}"
    json_path = out_dir / f"{slug}-raw.json"
    report_path = out_dir / f"{slug}竞品详细搜集-在营业机构.docx"
    map_path = out_dir / f"{slug}竞品地图-高德.html"

    search = [
        sys.executable,
        str(HERE / "search_competitors.py"),
        "--city",
        args.city,
        "--industry",
        args.industry,
        "--out",
        str(json_path),
        "--pages",
        str(args.pages),
    ]
    if args.keywords:
        search += ["--keywords", args.keywords]
    if args.env_file:
        search += ["--env-file", args.env_file]
    if args.exclude:
        search += ["--exclude", args.exclude]
    if args.expand_districts:
        search.append("--expand-districts")
    run(search)

    run([sys.executable, str(HERE / "build_report.py"), "--in-json", str(json_path), "--out", str(report_path)])
    run([sys.executable, str(HERE / "build_map.py"), "--in-json", str(json_path), "--out", str(map_path)])
    print("REPORT", report_path, flush=True)
    print("MAP", map_path, flush=True)
    print("JSON", json_path, flush=True)


if __name__ == "__main__":
    main()
