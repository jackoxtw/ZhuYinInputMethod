#!/usr/bin/env python3
"""Repair the bundled ZYT2S1 dictionary with OpenCC Taiwan variant core rules.

This is the offline fallback. The macOS installer builds the complete OpenCC
1.3.1 tw2s dictionary when the official source files can be fetched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from build_tw2s_opencc import parse_opencc
from zyt2s_format import convert_text, read_binary, write_binary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_bin")
    ap.add_argument("tw_variants")
    ap.add_argument("tw_variants_rev_phrases")
    ap.add_argument("output_bin")
    args = ap.parse_args()

    old_chars, old_phrase_list = read_binary(args.input_bin)
    old_phrases = dict(old_phrase_list)
    tw_variants = parse_opencc(args.tw_variants)
    rev_phrases = parse_opencc(args.tw_variants_rev_phrases)

    chars = dict(old_chars)
    phrases = dict(old_phrases)

    aliases = 0
    for standard, taiwan in tw_variants.items():
        if len(standard) != 1 or len(taiwan) != 1:
            continue
        simplified = old_chars.get(standard, standard)
        if chars.get(taiwan) != simplified:
            chars[taiwan] = simplified
            aliases += 1

    phrase_overrides = 0
    # Convert the canonical Traditional result using the original dictionary,
    # not the new Taiwan aliases, so self-preserving rules such as 著作 remain 著作.
    for taiwan_phrase, standard_phrase in rev_phrases.items():
        final_value = convert_text(standard_phrase, old_chars, old_phrase_list)
        charwise = "".join(chars.get(ch, ch) for ch in taiwan_phrase)
        if final_value != charwise:
            phrases[taiwan_phrase] = final_value
            phrase_overrides += 1

    count_chars, count_phrases, byte_count = write_binary(args.output_bin, chars, phrases)
    out_chars, out_phrases = read_binary(args.output_bin)
    probes = {
        "麵": "面",
        "牛肉麵": "牛肉面",
        "裡面": "里面",
        "為了": "为了",
        "著作": "著作",
        "看著": "看着",
    }
    for src, expected in probes.items():
        actual = convert_text(src, out_chars, out_phrases)
        if actual != expected:
            raise SystemExit(f"core repair validation failed: {src} -> {actual}, expected {expected}")

    print(
        f"Taiwan tw2s core repair: variant_aliases={aliases}, phrase_overrides={phrase_overrides}, "
        f"runtime_chars={count_chars}, runtime_phrases={count_phrases}"
    )
    print(f"output={args.output_bin} bytes={byte_count}")


if __name__ == "__main__":
    main()
