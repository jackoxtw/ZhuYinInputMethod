#!/usr/bin/env python3
"""Flatten OpenCC 1.3.1 tw2s dictionaries into the ZYT2S1 runtime format.

This follows tw2s.json's two conversion stages:
  1. Taiwan variants -> standard Traditional (TWVariantsRevPhrases + TWVariantsRev)
  2. Traditional -> Simplified (TSPhrases + TSCharacters)
The result is flattened into a phrase-first/character-fallback dictionary so the
input method has no runtime OpenCC dependency.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

from zyt2s_format import convert_text, read_binary, write_binary


def parse_opencc(path: str | Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for raw in Path(path).read_text("utf-8").splitlines():
        line = raw.strip("\ufeff\r\n")
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, values = line.split("\t", 1)
        first = values.strip().split(" ", 1)[0]
        if key and first:
            result[key] = first
    return result


def charwise(text: str, chars: Mapping[str, str]) -> str:
    return "".join(chars.get(ch, ch) for ch in text)


def taiwanize(text: str, std_to_tw: Mapping[str, str]) -> str:
    return "".join(std_to_tw.get(ch, ch) for ch in text)


def build_maps(
    ts_chars: Mapping[str, str],
    ts_phrases: Mapping[str, str],
    tw_variants: Mapping[str, str],
    tw_rev_phrases: Mapping[str, str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    # Stage 2 is standard Traditional -> Simplified.
    stage2_chars = {k: v for k, v in ts_chars.items() if len(k) == 1 and len(v) == 1}
    stage2_phrases = dict(ts_phrases)

    # TWVariants.txt is standard Traditional -> Taiwan Traditional. Reverse it.
    std_to_tw: Dict[str, str] = {}
    tw_to_std: Dict[str, str] = {}
    for std, tw in tw_variants.items():
        if len(std) == 1 and len(tw) == 1:
            std_to_tw[std] = tw
            tw_to_std[tw] = std

    # Runtime character fallback represents both stages composed together.
    final_chars = dict(stage2_chars)
    for tw, std in tw_to_std.items():
        final_chars[tw] = stage2_chars.get(std, std)

    final_phrases: Dict[str, str] = {}

    # Stage-2 phrase exceptions. Also emit a Taiwan-spelling alias, because stage 1
    # would canonicalize those characters before stage 2 sees them.
    for key, value in stage2_phrases.items():
        if value != charwise(key, final_chars):
            final_phrases[key] = value
        tw_key = taiwanize(key, std_to_tw)
        if tw_key != key and value != charwise(tw_key, final_chars):
            final_phrases[tw_key] = value

    # Stage-1 phrase rules have precedence over simple character reversal and over
    # the generated stage-2 aliases. Convert their standard-Traditional result
    # through the complete stage-2 converter.
    stage2_ordered = list(stage2_phrases.items())
    for tw_key, std_value in tw_rev_phrases.items():
        final_value = convert_text(std_value, stage2_chars, stage2_ordered)
        if final_value != charwise(tw_key, final_chars):
            final_phrases[tw_key] = final_value

    return final_chars, final_phrases


def validate_full(
    ts_chars: Mapping[str, str],
    ts_phrases: Mapping[str, str],
    tw_variants: Mapping[str, str],
    tw_rev_phrases: Mapping[str, str],
    final_chars: Mapping[str, str],
    final_phrases: Mapping[str, str],
) -> None:
    if len(ts_chars) < 4000:
        raise ValueError(f"TSCharacters too small: {len(ts_chars)}")
    # OpenCC 1.3.1 TSPhrases.txt is intentionally compact (281 entries).
    # Do not confuse it with STPhrases.txt, which is much larger.
    if len(ts_phrases) < 250:
        raise ValueError(f"TSPhrases too small: {len(ts_phrases)}")
    if len(tw_variants) < 30:
        raise ValueError(f"TWVariants too small: {len(tw_variants)}")
    if len(tw_rev_phrases) < 50:
        raise ValueError(f"TWVariantsRevPhrases too small: {len(tw_rev_phrases)}")

    # Validate characteristic entries from each immutable OpenCC 1.3.1 source
    # instead of relying on an inflated line-count assumption.
    source_probes = [
        ("TSCharacters", ts_chars, {"麵": "面", "裡": "里", "為": "为"}),
        ("TSPhrases", ts_phrases, {"計畫": "计划", "項鍊": "项链", "乾坤": "乾坤"}),
        ("TWVariants", tw_variants, {"麪": "麵", "裏": "裡", "爲": "為"}),
        ("TWVariantsRevPhrases", tw_rev_phrases, {"著作": "著作", "著名": "著名"}),
    ]
    for name, mapping, expected_entries in source_probes:
        for key, expected in expected_entries.items():
            actual = mapping.get(key)
            if actual != expected:
                raise ValueError(
                    f"{name} validation failed: {key} -> {actual!r}, expected {expected!r}"
                )

    probes = {
        "麵": "面",
        "裡面": "里面",
        "為了": "为了",
        "著作": "著作",
        "看著": "看着",
    }
    for src, expected in probes.items():
        actual = convert_text(src, final_chars, final_phrases)
        if actual != expected:
            raise ValueError(f"tw2s validation failed: {src} -> {actual}, expected {expected}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ts_characters")
    ap.add_argument("ts_phrases")
    ap.add_argument("tw_variants")
    ap.add_argument("tw_variants_rev_phrases")
    ap.add_argument("output")
    ap.add_argument("--require-full", action="store_true")
    args = ap.parse_args()

    ts_chars = parse_opencc(args.ts_characters)
    ts_phrases = parse_opencc(args.ts_phrases)
    tw_variants = parse_opencc(args.tw_variants)
    tw_rev_phrases = parse_opencc(args.tw_variants_rev_phrases)
    final_chars, final_phrases = build_maps(ts_chars, ts_phrases, tw_variants, tw_rev_phrases)

    if args.require_full:
        validate_full(ts_chars, ts_phrases, tw_variants, tw_rev_phrases, final_chars, final_phrases)

    char_count, phrase_count, byte_count = write_binary(args.output, final_chars, final_phrases)
    print(
        f"OpenCC tw2s overlay: ts_characters={len(ts_chars)}, ts_phrases={len(ts_phrases)}, "
        f"tw_variants={len(tw_variants)}, tw_reverse_phrases={len(tw_rev_phrases)}, "
        f"runtime_chars={char_count}, runtime_phrase_exceptions={phrase_count}"
    )
    print(f"output={args.output} bytes={byte_count}")


if __name__ == "__main__":
    main()
