#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from repair_dictionary_taiwan import read_dictionary

entries, _ = read_dictionary(ROOT / "Shared" / "Resources" / "dictionary.bin")
found = [e for e in entries if e.word == "逐音輸入法"]
assert len(found) == 1, f"expected exactly one 逐音輸入法 entry, got {len(found)}"
e = found[0]
assert e.pron == ("ㄓㄨˊ", "ㄧㄣ", "ㄕㄨ", "ㄖㄨˋ", "ㄈㄚˇ"), e.pron
assert e.weight == 200, e.weight
print("test_brand_word: OK")
