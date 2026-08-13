#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))
from zyt2s_format import convert_text, read_binary


def write(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def assert_cases(out: Path) -> None:
    chars, phrases = read_binary(out)
    cases = {
        "麵": "面",
        "牛肉麵": "牛肉面",
        "裡面": "里面",
        "為了": "为了",
        "著作": "著作",
        "看著": "看着",
    }
    for src, expected in cases.items():
        actual = convert_text(src, chars, phrases)
        assert actual == expected, (src, actual, expected)


def run_small_behavior_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ts_chars = d / "TSCharacters.txt"
        ts_phrases = d / "TSPhrases.txt"
        tw_variants = d / "TWVariants.txt"
        tw_rev = d / "TWVariantsRevPhrases.txt"
        out = d / "t2s.bin"

        write(ts_chars, """# synthetic\n麪\t面\n裏\t里\n爲\t为\n發\t发\n髮\t发\n飯\t饭\n臺\t台\n""")
        write(ts_phrases, """# synthetic\n頭髮\t头发\n發展\t发展\n""")
        write(tw_variants, """# synthetic\n麪\t麵\n裏\t裡\n爲\t為\n着\t著\n""")
        write(tw_rev, """# synthetic\n著作\t著作\n著名\t著名\n""")

        subprocess.run(
            [sys.executable, str(ROOT / "Tools" / "build_tw2s_opencc.py"),
             str(ts_chars), str(ts_phrases), str(tw_variants), str(tw_rev), str(out)],
            check=True,
        )
        assert_cases(out)
        chars, phrases = read_binary(out)
        assert convert_text("頭髮", chars, phrases) == "头发"
        assert convert_text("著名", chars, phrases) == "著名"


def run_require_full_shape_test() -> None:
    """Exercise --require-full without network by making official-sized fixtures."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ts_chars = d / "TSCharacters.txt"
        ts_phrases = d / "TSPhrases.txt"
        tw_variants = d / "TWVariants.txt"
        tw_rev = d / "TWVariantsRevPhrases.txt"
        out = d / "t2s.bin"

        char_lines = ["麵\t面", "麪\t面", "裡\t里", "裏\t里", "為\t为", "爲\t为", "發\t发", "髮\t发"]
        # 4,100 distinct BMP characters are enough to exercise the production gate.
        for cp in range(0x3400, 0x3400 + 4100):
            ch = chr(cp)
            char_lines.append(f"{ch}\t{ch}")
        write(ts_chars, "\n".join(char_lines) + "\n")

        phrase_lines = [
            "計畫\t计划",
            "項鍊\t项链",
            "乾坤\t乾坤",
        ] + [f"測試詞{i}\t測試詞{i}" for i in range(278)]
        write(ts_phrases, "\n".join(phrase_lines) + "\n")

        variant_lines = ["麪\t麵", "裏\t裡", "爲\t為", "着\t著"]
        # Add harmless distinct one-character variants to cross the production threshold.
        for i in range(30):
            variant_lines.append(f"{chr(0x7000+i)}\t{chr(0x7100+i)}")
        write(tw_variants, "\n".join(variant_lines) + "\n")

        rev_lines = ["著作\t著作", "著名\t著名"] + [f"例外詞{i}\t例外詞{i}" for i in range(54)]
        write(tw_rev, "\n".join(rev_lines) + "\n")

        subprocess.run(
            [sys.executable, str(ROOT / "Tools" / "build_tw2s_opencc.py"),
             str(ts_chars), str(ts_phrases), str(tw_variants), str(tw_rev), str(out),
             "--require-full"],
            check=True,
        )
        assert_cases(out)


def main() -> None:
    run_small_behavior_test()
    run_require_full_shape_test()
    print("test_opencc_tw2s_build: OK")


if __name__ == "__main__":
    main()
