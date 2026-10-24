#!/usr/bin/env python3
"""Synchronize the Canvas single-file HTML dictionary payload from ZYDICT2.

The HTML payload also contains Traditional->Simplified conversion data.  This
script preserves those fields and replaces only the dictionary-related fields,
so native and HTML builds share the same offline dictionary entries/readings.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
from pathlib import Path

MAGIC = b"ZYDICT2\0"
FMT = "<8sIIIIII" + "Q" * 15
HEADER_SIZE = struct.calcsize(FMT)
PAYLOAD_RE = re.compile(r"(const payload\s*=\s*)(\{.*?\})(;\s*\n)", re.S)


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def u32_values(data: bytes, off: int, count: int) -> tuple[int, ...]:
    return struct.unpack_from(f"<{count}I", data, off)


def parse_dictionary(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < HEADER_SIZE:
        raise ValueError(f"dictionary is too small: {path}")
    h = struct.unpack_from(FMT, data, 0)
    (
        magic, version, header_size, word_count, indexed_word_count,
        syllable_count, bucket_count, file_size,
        word_pool_off, word_pool_size, word_offsets_off, pron_offsets_off,
        syllable_ids_off, syllable_ids_count, weights_off,
        syllable_pool_off, syllable_pool_size, syllable_offsets_off,
        bucket_symbols_off, bucket_offsets_off, bucket_word_ids_off,
        bucket_word_ids_count,
    ) = h
    if magic != MAGIC or version != 2 or header_size != HEADER_SIZE or file_size != len(data):
        raise ValueError(f"unsupported or damaged ZYDICT2: {path}")

    def section(off: int, size: int) -> bytes:
        end = off + size
        if off < HEADER_SIZE or end > len(data):
            raise ValueError(f"dictionary section out of range: off={off}, size={size}")
        return data[off:end]

    word_pool = section(word_pool_off, word_pool_size)
    word_offsets = section(word_offsets_off, (word_count + 1) * 4)
    pron_offsets = section(pron_offsets_off, (word_count + 1) * 4)
    syllable_ids = section(syllable_ids_off, syllable_ids_count * 2)
    weights = section(weights_off, word_count)
    syllable_offsets_raw = section(syllable_offsets_off, (syllable_count + 1) * 4)
    syllable_offsets = u32_values(data, syllable_offsets_off, syllable_count + 1)
    syllables = []
    for i in range(syllable_count):
        a, b = syllable_offsets[i], syllable_offsets[i + 1]
        if b < a or b > syllable_pool_size:
            raise ValueError("invalid syllable offsets")
        syllables.append(data[syllable_pool_off + a:syllable_pool_off + b].decode("utf-8"))

    bucket_symbols_raw = section(bucket_symbols_off, bucket_count * 4)
    bucket_symbols = "".join(chr(cp) for cp in struct.unpack(f"<{bucket_count}I", bucket_symbols_raw))
    bucket_offsets = section(bucket_offsets_off, (bucket_count + 1) * 4)
    bucket_word_ids = section(bucket_word_ids_off, bucket_word_ids_count * 4)

    # HTML core stores 32-bit bucket IDs.  Keep this explicit because word_count
    # has exceeded 65535 for several releases.
    return {
        "word_count": word_count,
        "indexed_word_count": indexed_word_count,
        "word_pool_b64": b64(word_pool),
        "word_offsets_b64": b64(word_offsets),
        "pron_offsets_b64": b64(pron_offsets),
        "syllable_ids_b64": b64(syllable_ids),
        "weights_b64": b64(weights),
        "syllable_table": syllables,
        "bucket_symbols": bucket_symbols,
        "bucket_offsets_b64": b64(bucket_offsets),
        "bucket_word_ids_b64": b64(bucket_word_ids),
        "bucket_word_id_bits": 32,
    }


def sync(html_path: Path, dictionary_path: Path) -> dict:
    source = html_path.read_text(encoding="utf-8")
    m = PAYLOAD_RE.search(source)
    if not m:
        raise ValueError(f"cannot find const payload in {html_path}")
    payload = json.loads(m.group(2))
    dictionary_payload = parse_dictionary(dictionary_path)
    payload.update(dictionary_payload)
    packed = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    updated = source[:m.start()] + m.group(1) + packed + m.group(3) + source[m.end():]
    html_path.write_text(updated, encoding="utf-8")
    return {
        "word_count": dictionary_payload["word_count"],
        "indexed_word_count": dictionary_payload["indexed_word_count"],
        "syllable_count": len(dictionary_payload["syllable_table"]),
        "bucket_count": len(dictionary_payload["bucket_symbols"]),
        "html_bytes": html_path.stat().st_size,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("dictionary", type=Path)
    args = ap.parse_args()
    stats = sync(args.html, args.dictionary)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
