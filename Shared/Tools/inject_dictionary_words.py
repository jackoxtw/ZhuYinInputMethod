#!/usr/bin/env python3
"""Inject or update data-driven words in a ZYDICT1 dictionary."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from repair_dictionary_taiwan import Entry, read_dictionary, write_dictionary


def read_extra_words(path: Path) -> list[Entry]:
    out: list[Entry] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            row = [x.strip() for x in row]
            if len(row) < 4:
                raise ValueError(f"invalid extra-word row: {row!r}")
            word = row[0]
            weight = int(row[1])
            pron = tuple(x for x in row[2:] if x)
            if not word or not pron:
                raise ValueError(f"invalid extra-word row: {row!r}")
            out.append(Entry(word, pron, max(0, min(255, weight))))
    return out


def inject(entries: list[Entry], extra: list[Entry]) -> tuple[list[Entry], int, int]:
    index = {(e.word, e.pron): i for i, e in enumerate(entries)}
    added = updated = 0
    for e in extra:
        key = (e.word, e.pron)
        i = index.get(key)
        if i is None:
            index[key] = len(entries)
            entries.append(e)
            added += 1
        elif entries[i].weight != e.weight:
            entries[i] = e
            updated += 1
    return entries, added, updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("words_csv", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    entries, syllables = read_dictionary(args.input)
    extra = read_extra_words(args.words_csv)
    if not extra:
        raise SystemExit(f"no extra words parsed from {args.words_csv}")
    entries, added, updated = inject(entries, extra)
    write_dictionary(args.output, entries, syllables)
    print(f"dictionary extra words: added={added}, updated={updated}, total={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
