#!/usr/bin/env python3
"""Build the offline proper-noun/transport word layer for 逐音輸入法.

The generator keeps large source lists as compact name-only CSV files and derives
pronunciations from the bundled Taiwan dictionary at build time.  This avoids
shipping a second pronunciation table while keeping installation fully offline.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import OrderedDict
from pathlib import Path

from repair_dictionary_taiwan import read_dictionary

# Proper-name readings that differ from the general/default character reading.
# These overrides are intentionally narrow: only characters with well-known
# Taiwan place-name readings live here; the rest uses the dictionary's highest
# weighted single-character reading.
GEO_CHAR_OVERRIDES = {
    "重": "ㄔㄨㄥˊ",   # 三重、重慶路
    "長": "ㄔㄤˊ",    # 元長、長治、長濱、長安路
    "埔": "ㄆㄨˇ",    # 埔里、新埔、北埔、中埔、內埔、鹽埔、埔心、埔鹽
    "朴": "ㄆㄨˊ",    # 朴子
    "茄": "ㄑㄧㄝˊ",  # 茄萣
    "地": "ㄉㄧˋ",    # 三地門、瓜地馬拉
    # CNS / legacy road-name glyphs missing from the compact single-char layer.
    "双": "ㄕㄨㄤ",
    "响": "ㄒㄧㄤˇ",
    "尫": "ㄨㄤ",
    "廍": "ㄅㄨˋ",
    "拕": "ㄊㄨㄛ",
    "梹": "ㄅㄧㄣ",
    "硘": "ㄏㄨㄟˊ",
    "磘": "ㄧㄠˊ",
    "羗": "ㄑㄧㄤ",
    "脚": "ㄐㄧㄠˇ",
    "舘": "ㄍㄨㄢˇ",
    "鮘": "ㄉㄞˋ",
}

ROAD_SECTION_RE = re.compile(r"[0-9０-９零〇一二三四五六七八九十百]+段")
HAN_RUN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


def _unique_csv_column(path: Path, column: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            value = (row.get(column) or "").strip()
            if value and value not in seen:
                seen.add(value)
                out.append(value)
    return out


def load_admin(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            county = (row.get("county") or "").strip()
            district = (row.get("district") or "").strip()
            if county and district:
                rows.append((county, district))
    counties = {c for c, _ in rows}
    if len(counties) != 22 or len(rows) != 368:
        raise ValueError(
            "Taiwan admin source must contain 22 counties/cities and 368 districts; "
            f"got {len(counties)} / {len(rows)}"
        )
    return rows


def load_countries(path: Path) -> list[str]:
    out = _unique_csv_column(path, "name")
    if len(out) < 100:
        raise ValueError(f"common country/region source looks incomplete: only {len(out)} names")
    return out


def load_road_names(path: Path) -> list[str]:
    out = _unique_csv_column(path, "name")
    if len(out) < 10_000:
        raise ValueError(f"Taiwan road source looks incomplete: only {len(out)} names")
    bad = [n for n in out if ROAD_SECTION_RE.search(n)]
    if bad:
        raise ValueError(f"road source must contain main names only (no 段): first={bad[0]!r}")
    bad_suffix = [n for n in out if not n.endswith(("路", "街", "大道"))]
    if bad_suffix:
        raise ValueError(f"road source contains non-road name: first={bad_suffix[0]!r}")
    return out


def load_stations(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            system = (row.get("system") or "").strip()
            name = (row.get("name") or "").strip()
            key = (system, name)
            if system and name and key not in seen:
                seen.add(key)
                out.append(key)
    if len(out) < 500:
        raise ValueError(f"Taiwan rail/transit station source looks incomplete: only {len(out)} rows")
    return out


def load_airports(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            kind = (row.get("kind") or "alias").strip() or "alias"
            key = (name, kind)
            if name and key not in seen:
                seen.add(key)
                out.append(key)
    official = {name for name, kind in out if kind == "official"}
    if len(official) != 17:
        raise ValueError(f"Taiwan airport source must contain the 17 CAA airports; got {len(official)}")
    return out


def build_primary_readings(dictionary: Path) -> dict[str, str]:
    entries, _ = read_dictionary(dictionary)
    choices: dict[str, tuple[int, int, str]] = {}
    for order, entry in enumerate(entries):
        if len(entry.word) != 1 or len(entry.pron) != 1:
            continue
        current = choices.get(entry.word)
        candidate = (entry.weight, -order, entry.pron[0])
        if current is None or candidate[:2] > current[:2]:
            choices[entry.word] = candidate
    return {char: value[2] for char, value in choices.items()}


def pronunciation(word: str, primary: dict[str, str]) -> tuple[str, ...]:
    out: list[str] = []
    for ch in word:
        reading = GEO_CHAR_OVERRIDES.get(ch) or primary.get(ch)
        if not reading:
            raise ValueError(f"missing single-character reading for {ch!r} in {word!r}")
        out.append(reading)
    return tuple(out)


def tai_variants(word: str) -> list[str]:
    """Return official spelling plus common 台 spellings for every 臺 position."""
    variants = [word]
    positions = [i for i, ch in enumerate(word) if ch == "臺"]
    for mask in range(1, 1 << len(positions)):
        chars = list(word)
        for bit, pos in enumerate(positions):
            if mask & (1 << bit):
                chars[pos] = "台"
        variants.append("".join(chars))
    return variants


def add_word(
    store: OrderedDict[tuple[str, tuple[str, ...]], int],
    word: str,
    weight: int,
    primary: dict[str, str],
) -> None:
    for variant in tai_variants(word):
        pron = pronunciation(variant, primary)
        key = (variant, pron)
        store[key] = max(weight, store.get(key, 0))


def station_name_parts(name: str) -> list[str]:
    """Return IME-friendly Han-only aliases from a displayed station name.

    Parenthetical/slash labels such as「新城 (太魯閣)」and「廣慈/奉天宮」
    become separate searchable aliases.  Numeric branding (台北101/世貿) keeps
    the Han runs (台北、世貿) instead of inventing a spoken form for digits.
    """
    out: list[str] = []
    for part in HAN_RUN_RE.findall(name):
        part = part.strip()
        if len(part) >= 2 and part not in out:
            out.append(part)
    return out


def _station_base_and_forms(name: str) -> tuple[str, list[str]]:
    forms: list[str] = []
    if name.endswith("車站") and len(name) > 2:
        base = name[:-2]
        forms.extend([name, base, base + "站"])
    elif name.endswith("站") and len(name) > 1:
        base = name[:-1]
        forms.extend([name, base])
    else:
        base = name
        forms.extend([base, base + "站"])
    return base, list(dict.fromkeys(forms))


def add_station_words(
    out: OrderedDict[tuple[str, tuple[str, ...]], int],
    system: str,
    display_name: str,
    primary: dict[str, str],
) -> None:
    for part in station_name_parts(display_name):
        base, forms = _station_base_and_forms(part)
        if len(base) < 2:
            continue
        # Preserve the source spelling (including 車站 where supplied), plus a
        # compact bare-name/「站」alias for composition and recall.
        for form in forms:
            add_word(out, form, 205 if form.endswith("站") else 185, primary)

        if system == "tra_sched":
            add_word(out, base + "車站", 205, primary)
            add_word(out, "臺鐵" + base + "站", 215, primary)
        elif system == "thsr_sched":
            add_word(out, base + "車站", 200, primary)
            add_word(out, "高鐵" + base + "站", 220, primary)
        elif system == "tymc":
            add_word(out, "機捷" + base + "站", 215, primary)
            add_word(out, "桃園捷運" + base + "站", 210, primary)
        elif system in {"mrt", "ntdlrt", "ntalrt", "sanying", "krtc", "tmrt"}:
            add_word(out, "捷運" + base + "站", 210, primary)
            if system in {"ntdlrt", "ntalrt", "krtc"}:
                add_word(out, "輕軌" + base + "站", 205, primary)
        elif system == "afr_sched":
            add_word(out, base + "車站", 195, primary)
            add_word(out, "阿里山" + base + "站", 205, primary)


def build_words(
    dictionary: Path,
    admin_csv: Path,
    countries_csv: Path,
    roads_csv: Path | None = None,
    stations_csv: Path | None = None,
    airports_csv: Path | None = None,
) -> OrderedDict[tuple[str, tuple[str, ...]], int]:
    primary = build_primary_readings(dictionary)
    admin = load_admin(admin_csv)
    countries = load_countries(countries_csv)
    out: OrderedDict[tuple[str, tuple[str, ...]], int] = OrderedDict()

    counties: list[str] = []
    for county, _ in admin:
        if county not in counties:
            counties.append(county)
    for county in counties:
        add_word(out, county, 220, primary)
        short = county[:-1]
        if len(short) >= 2:
            add_word(out, short, 195, primary)

    for county, district in admin:
        add_word(out, district, 210, primary)
        base = district[:-1]
        if len(base) >= 2:
            add_word(out, base, 185, primary)
            add_word(out, county + base, 205, primary)
        add_word(out, county + district, 225, primary)

    for name in countries:
        add_word(out, name, 205, primary)

    if roads_csv is not None:
        # Main road names intentionally omit section suffixes (一段／二段…).
        # Keep their weight below administrative names and transport hubs so a
        # large road list does not dominate ordinary candidate ranking.
        for name in load_road_names(roads_csv):
            add_word(out, name, 165, primary)

    if stations_csv is not None:
        for system, name in load_stations(stations_csv):
            add_station_words(out, system, name, primary)

    if airports_csv is not None:
        for name, kind in load_airports(airports_csv):
            add_word(out, name, 225 if kind == "official" else 205, primary)

    return out


def write_words(path: Path, words: OrderedDict[tuple[str, tuple[str, ...]], int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("# word,weight,syllables...\n")
        writer = csv.writer(f)
        for (word, pron), weight in words.items():
            writer.writerow([word, weight, *pron])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dictionary", type=Path)
    ap.add_argument("admin_csv", type=Path)
    ap.add_argument("countries_csv", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--roads-csv", type=Path)
    ap.add_argument("--stations-csv", type=Path)
    ap.add_argument("--airports-csv", type=Path)
    args = ap.parse_args()
    words = build_words(
        args.dictionary,
        args.admin_csv,
        args.countries_csv,
        args.roads_csv,
        args.stations_csv,
        args.airports_csv,
    )
    write_words(args.output, words)
    print(f"geographic/transport words: {len(words)} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
