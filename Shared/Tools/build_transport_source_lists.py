#!/usr/bin/env python3
"""Normalize externally downloaded Taiwan road/station snapshots into compact CSVs.

This helper intentionally performs no network access.  Download/update source snapshots
separately, then run this script so the shipped IME resources remain deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

SECTION_RE = re.compile(r"[0-9０-９零〇一二三四五六七八九十百]+段")
TRAILING_SECTION_RE = re.compile(r"[0-9一二三四五六七八九十百]+段$")


def normalize_fullwidth_digits(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def normalize_road(name: str) -> str | None:
    name = normalize_fullwidth_digits(name.strip())
    if name.endswith("臨"):
        name = name[:-1]
    name = TRAILING_SECTION_RE.sub("", name).strip()
    # A few source rows describe side streets whose own name still embeds a
    # numbered section (e.g. 「豐原大道1段…街」).  They are intentionally omitted
    # because this project stores only section-free main road names.
    if SECTION_RE.search(name):
        return None
    if len(name) < 2 or not name.endswith(("路", "街", "大道")):
        return None
    return name


def build_roads(source: Path, output: Path) -> int:
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    names: set[str] = set()
    for city in data:
        for area in city.get("AreaList", []):
            for row in area.get("RoadList", []):
                name = normalize_road(str(row.get("RoadName", "")))
                if name:
                    names.add(name)
    ordered = sorted(names)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name"])
        w.writerows((name,) for name in ordered)
    return len(ordered)


def build_stations(source: Path, output: Path) -> int:
    obj = json.loads(source.read_text(encoding="utf-8-sig"))
    rows: set[tuple[str, str]] = set()
    for feature in obj.get("features", []):
        props = feature.get("properties") or {}
        system = str(props.get("sys", "")).strip()
        name = str(props.get("name", "")).strip()
        if system and name:
            rows.add((system, name))
    ordered = sorted(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["system", "name"])
        w.writerows(ordered)
    return len(ordered)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--road-json", type=Path)
    ap.add_argument("--road-output", type=Path)
    ap.add_argument("--station-geojson", type=Path)
    ap.add_argument("--station-output", type=Path)
    args = ap.parse_args()

    if bool(args.road_json) != bool(args.road_output):
        ap.error("--road-json and --road-output must be used together")
    if bool(args.station_geojson) != bool(args.station_output):
        ap.error("--station-geojson and --station-output must be used together")
    if not args.road_json and not args.station_geojson:
        ap.error("provide a road or station source")

    if args.road_json:
        print(f"road main names: {build_roads(args.road_json, args.road_output)} -> {args.road_output}")
    if args.station_geojson:
        print(f"station rows: {build_stations(args.station_geojson, args.station_output)} -> {args.station_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
