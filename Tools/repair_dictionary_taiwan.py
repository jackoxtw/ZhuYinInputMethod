#!/usr/bin/env python3
"""Overlay Taiwan single-character readings onto an existing ZYDICT1 dictionary.

Existing word IDs are preserved.  When a character has multiple Taiwan readings,
the existing ID keeps its matching reading (or is reassigned to the first Taiwan
reading if the old reading is not valid in the Taiwan source) and additional
readings are appended as new IDs.
"""
from __future__ import annotations

import argparse
import csv
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"ZYDICT1\0"
FMT = "<8sIIIIII" + "Q" * 15
HEADER_SIZE = struct.calcsize(FMT)


@dataclass
class Entry:
    word: str
    pron: tuple[str, ...]
    weight: int


def _unpack_u32(data: bytes, off: int, count: int) -> tuple[int, ...]:
    return struct.unpack_from(f"<{count}I", data, off)


def _unpack_u16(data: bytes, off: int, count: int) -> tuple[int, ...]:
    return struct.unpack_from(f"<{count}H", data, off)


def read_dictionary(path: Path) -> tuple[list[Entry], list[str]]:
    data = path.read_bytes()
    h = struct.unpack_from(FMT, data, 0)
    (magic, version, header_size, word_count, indexed_word_count, syllable_count, bucket_count,
     file_size, word_pool_off, word_pool_size, word_offsets_off, pron_offsets_off,
     syllable_ids_off, syllable_ids_count, weights_off, syllable_pool_off, syllable_pool_size,
     syllable_offsets_off, bucket_symbols_off, bucket_offsets_off, bucket_word_ids_off,
     bucket_word_ids_count) = h
    if not magic.startswith(b"ZYDICT1") or version != 1 or header_size != HEADER_SIZE or file_size != len(data):
        raise ValueError(f"unsupported or damaged dictionary: {path}")

    word_offsets = _unpack_u32(data, word_offsets_off, word_count + 1)
    pron_offsets = _unpack_u32(data, pron_offsets_off, word_count + 1)
    syllable_ids = _unpack_u16(data, syllable_ids_off, syllable_ids_count)
    syllable_offsets = _unpack_u32(data, syllable_offsets_off, syllable_count + 1)
    weights = data[weights_off:weights_off + word_count]

    syllables: list[str] = []
    for i in range(syllable_count):
        a, b = syllable_offsets[i], syllable_offsets[i + 1]
        syllables.append(data[syllable_pool_off + a:syllable_pool_off + b].decode("utf-8"))

    entries: list[Entry] = []
    for wid in range(word_count):
        a, b = word_offsets[wid], word_offsets[wid + 1]
        word = data[word_pool_off + a:word_pool_off + b].decode("utf-8")
        pa, pb = pron_offsets[wid], pron_offsets[wid + 1]
        pron = tuple(syllables[syllable_ids[j]] for j in range(pa, pb))
        entries.append(Entry(word, pron, weights[wid]))
    return entries, syllables


def _looks_zhuyin(value: str) -> bool:
    if not value:
        return False
    allowed_tones = {"ˊ", "ˇ", "ˋ", "˙"}
    seen = False
    for ch in value:
        cp = ord(ch)
        if 0x3105 <= cp <= 0x312F or 0x31A0 <= cp <= 0x31BF:
            seen = True
            continue
        if ch in allowed_tones:
            continue
        return False
    return seen


def read_taiwan_readings(path: Path) -> dict[str, list[str]]:
    readings: dict[str, list[str]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            row = [x.strip() for x in row]
            char = pron = None
            # Current libchewing-data source: Character,Category,Bopomofo
            if len(row) >= 3 and row[1].isdigit() and _looks_zhuyin(row[2]):
                char, pron = row[0], row[2]
            # Older libchewing-data layout: Category,Bopomofo,Character
            elif len(row) >= 3 and row[0].isdigit() and _looks_zhuyin(row[1]):
                char, pron = row[2], row[1]
            if not char or not pron or len(char) != 1:
                continue
            if pron not in readings[char]:
                readings[char].append(pron)
    return dict(readings)


def overlay(entries: list[Entry], readings: dict[str, list[str]]) -> tuple[list[Entry], dict[str, int]]:
    by_char: dict[str, list[int]] = defaultdict(list)
    for i, e in enumerate(entries):
        if len(e.word) == 1:
            by_char[e.word].append(i)

    appended = 0
    corrected = 0
    polyphonic = 0
    covered = 0

    for char, source_readings in readings.items():
        ids = by_char.get(char)
        if not ids:
            continue
        # Only single-syllable rows belong in the character overlay.
        source = list(dict.fromkeys(source_readings))
        if not source:
            continue
        covered += 1
        if len(source) > 1:
            polyphonic += 1

        used: set[str] = set()
        unmatched_ids: list[int] = []
        for wid in ids:
            old = entries[wid]
            old_pron = old.pron[0] if len(old.pron) == 1 else None
            if old_pron in source and old_pron not in used:
                used.add(old_pron)
            else:
                unmatched_ids.append(wid)

        remaining = [r for r in source if r not in used]
        # Reuse old IDs first so learning data keyed by word ID stays attached to the same word.
        for wid in unmatched_ids:
            if remaining:
                new_pron = remaining.pop(0)
                if entries[wid].pron != (new_pron,):
                    entries[wid] = Entry(entries[wid].word, (new_pron,), entries[wid].weight)
                    corrected += 1
                used.add(new_pron)
            elif source:
                # More legacy duplicate IDs than Taiwan readings: keep the ID valid but duplicate
                # the primary reading rather than retaining a non-Taiwan pronunciation.
                new_pron = source[0]
                if entries[wid].pron != (new_pron,):
                    entries[wid] = Entry(entries[wid].word, (new_pron,), entries[wid].weight)
                    corrected += 1

        base_weight = max(entries[wid].weight for wid in ids)
        for r in remaining:
            entries.append(Entry(char, (r,), base_weight))
            appended += 1

    return entries, {
        "covered_characters": covered,
        "corrected_existing_ids": corrected,
        "polyphonic_characters": polyphonic,
        "appended_readings": appended,
    }


def _align8(buf: bytearray) -> None:
    while len(buf) % 8:
        buf.append(0)


def _put(buf: bytearray, raw: bytes) -> int:
    _align8(buf)
    off = len(buf)
    buf.extend(raw)
    return off


def _pack_u32(values: list[int]) -> bytes:
    return struct.pack(f"<{len(values)}I", *values) if values else b""


def _pack_u16(values: list[int]) -> bytes:
    return struct.pack(f"<{len(values)}H", *values) if values else b""


def write_dictionary(path: Path, entries: list[Entry], original_syllables: list[str]) -> None:
    syllables = list(original_syllables)
    syllable_id = {s: i for i, s in enumerate(syllables)}
    for e in entries:
        for s in e.pron:
            if s not in syllable_id:
                syllable_id[s] = len(syllables)
                syllables.append(s)

    word_pool = bytearray()
    word_offsets = [0]
    pron_offsets = [0]
    all_syllable_ids: list[int] = []
    weights = bytearray()
    buckets: dict[int, list[int]] = defaultdict(list)

    for wid, e in enumerate(entries):
        raw = e.word.encode("utf-8")
        word_pool.extend(raw)
        word_offsets.append(len(word_pool))
        for s in e.pron:
            all_syllable_ids.append(syllable_id[s])
        pron_offsets.append(len(all_syllable_ids))
        weights.append(max(0, min(255, int(e.weight))))
        if e.pron and e.pron[0]:
            buckets[ord(e.pron[0][0])].append(wid)

    syllable_pool = bytearray()
    syllable_offsets = [0]
    for s in syllables:
        syllable_pool.extend(s.encode("utf-8"))
        syllable_offsets.append(len(syllable_pool))

    bucket_symbols = sorted(buckets)
    bucket_offsets = [0]
    bucket_word_ids: list[int] = []
    for cp in bucket_symbols:
        bucket_word_ids.extend(buckets[cp])
        bucket_offsets.append(len(bucket_word_ids))

    buf = bytearray(b"\0" * HEADER_SIZE)
    word_pool_off = _put(buf, bytes(word_pool)); word_pool_size = len(word_pool)
    word_offsets_off = _put(buf, _pack_u32(word_offsets))
    pron_offsets_off = _put(buf, _pack_u32(pron_offsets))
    syllable_ids_off = _put(buf, _pack_u16(all_syllable_ids)); syllable_ids_count = len(all_syllable_ids)
    weights_off = _put(buf, bytes(weights))
    syllable_pool_off = _put(buf, bytes(syllable_pool)); syllable_pool_size = len(syllable_pool)
    syllable_offsets_off = _put(buf, _pack_u32(syllable_offsets))
    bucket_symbols_off = _put(buf, _pack_u32(bucket_symbols))
    bucket_offsets_off = _put(buf, _pack_u32(bucket_offsets))
    bucket_word_ids_off = _put(buf, _pack_u32(bucket_word_ids)); bucket_word_ids_count = len(bucket_word_ids)
    file_size = len(buf)
    indexed_word_count = sum(1 for e in entries if e.pron)

    header = struct.pack(
        FMT, MAGIC, 1, HEADER_SIZE, len(entries), indexed_word_count, len(syllables), len(bucket_symbols),
        file_size, word_pool_off, word_pool_size, word_offsets_off, pron_offsets_off,
        syllable_ids_off, syllable_ids_count, weights_off, syllable_pool_off, syllable_pool_size,
        syllable_offsets_off, bucket_symbols_off, bucket_offsets_off, bucket_word_ids_off, bucket_word_ids_count,
    )
    buf[:HEADER_SIZE] = header
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("taiwan_csv", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--require-full", action="store_true", help="reject a partial/core Taiwan source")
    args = ap.parse_args()

    entries, syllables = read_dictionary(args.input)
    readings = read_taiwan_readings(args.taiwan_csv)
    if not readings:
        raise SystemExit(f"no Taiwan readings parsed from {args.taiwan_csv}")
    # Guard against accidentally downloading an HTML error page or an unrelated/partial CSV.
    if "期" not in readings or "ㄑㄧˊ" not in readings["期"]:
        raise SystemExit("Taiwan reading source failed sanity check: 期 must include ㄑㄧˊ")
    if args.require_full and len(readings) < 5000:
        raise SystemExit(f"Taiwan reading source looks incomplete: only {len(readings)} characters")

    entries, stats = overlay(entries, readings)
    write_dictionary(args.output, entries, syllables)
    print("Taiwan dictionary overlay:", ", ".join(f"{k}={v}" for k, v in stats.items()))
    print(f"output={args.output} words={len(entries)} bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
