#!/usr/bin/env python3
"""Read/write the compact ZYT2S1 runtime dictionary used by 逐音輸入法."""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

MAGIC = b"ZYT2S1\0\0"
HFMT = "<8sIIIIQQQQQQ"
RFMT = "<IIII"
HS = struct.calcsize(HFMT)
RS = struct.calcsize(RFMT)


def _align8(buf: bytearray) -> None:
    while len(buf) % 8:
        buf.append(0)


def _put(buf: bytearray, data: bytes) -> int:
    _align8(buf)
    off = len(buf)
    buf.extend(data)
    return off


def read_binary(path: str | Path) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
    data = Path(path).read_bytes()
    if len(data) < HS:
        raise ValueError("ZYT2S1 file is truncated")
    (
        magic,
        version,
        char_count,
        phrase_count,
        header_size,
        file_size,
        trad_off,
        simp_off,
        records_off,
        pool_off,
        pool_size,
    ) = struct.unpack_from(HFMT, data, 0)
    if magic != MAGIC or version != 1 or header_size != HS or file_size != len(data):
        raise ValueError("invalid ZYT2S1 header")
    if pool_off + pool_size > len(data):
        raise ValueError("invalid ZYT2S1 pool")

    trad = struct.unpack_from(f"<{char_count}I", data, trad_off) if char_count else ()
    simp = struct.unpack_from(f"<{char_count}I", data, simp_off) if char_count else ()
    chars = {chr(a): chr(b) for a, b in zip(trad, simp)}

    pool = data[pool_off : pool_off + pool_size]
    phrases: List[Tuple[str, str]] = []
    for i in range(phrase_count):
        ao, al, bo, bl = struct.unpack_from(RFMT, data, records_off + i * RS)
        a = pool[ao : ao + al].decode("utf-8")
        b = pool[bo : bo + bl].decode("utf-8")
        phrases.append((a, b))
    return chars, phrases


def write_binary(
    path: str | Path,
    chars: Mapping[str, str],
    phrases: Mapping[str, str] | Iterable[Tuple[str, str]],
) -> Tuple[int, int, int]:
    cmap = sorted((ord(a), ord(b)) for a, b in chars.items() if len(a) == 1 and len(b) == 1)
    trad = struct.pack(f"<{len(cmap)}I", *[a for a, _ in cmap]) if cmap else b""
    simp = struct.pack(f"<{len(cmap)}I", *[b for _, b in cmap]) if cmap else b""

    phrase_items = list(phrases.items()) if isinstance(phrases, Mapping) else list(phrases)
    # Last value for an exact key wins, then longest UTF-8 key first to match the C runtime scan.
    dedup: Dict[str, str] = {}
    for key, value in phrase_items:
        if key and value:
            dedup[key] = value
    ordered = sorted(dedup.items(), key=lambda kv: (-len(kv[0].encode("utf-8")), kv[0]))

    pool = bytearray()
    recs = []
    for key, value in ordered:
        kb = key.encode("utf-8")
        vb = value.encode("utf-8")
        ko = len(pool)
        pool.extend(kb)
        vo = len(pool)
        pool.extend(vb)
        recs.append((ko, len(kb), vo, len(vb)))
    recb = b"".join(struct.pack(RFMT, *r) for r in recs)

    buf = bytearray(b"\0" * HS)
    trad_off = _put(buf, trad)
    simp_off = _put(buf, simp)
    records_off = _put(buf, recb)
    pool_off = _put(buf, bytes(pool))
    file_size = len(buf)
    buf[:HS] = struct.pack(
        HFMT,
        MAGIC,
        1,
        len(cmap),
        len(recs),
        HS,
        file_size,
        trad_off,
        simp_off,
        records_off,
        pool_off,
        len(pool),
    )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(buf)
    return len(cmap), len(recs), file_size


def convert_text(text: str, chars: Mapping[str, str], phrases: Sequence[Tuple[str, str]] | Mapping[str, str]) -> str:
    if isinstance(phrases, Mapping):
        ordered = sorted(phrases.items(), key=lambda kv: (-len(kv[0].encode("utf-8")), kv[0]))
    else:
        ordered = list(phrases)
        ordered.sort(key=lambda kv: (-len(kv[0].encode("utf-8")), kv[0]))
    by_first: Dict[str, List[Tuple[str, str]]] = {}
    for key, value in ordered:
        if key:
            by_first.setdefault(key[0], []).append((key, value))

    out: List[str] = []
    i = 0
    while i < len(text):
        matched = False
        for key, value in by_first.get(text[i], ()):
            if text.startswith(key, i):
                out.append(value)
                i += len(key)
                matched = True
                break
        if not matched:
            out.append(chars.get(text[i], text[i]))
            i += 1
    return "".join(out)
