"""Ensure the single-file HTML embeds exactly the bundled ZYDICT2 dictionary."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from build_native_dictionary import build

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html"
DICT = ROOT / "Shared/Resources/dictionary.bin"

source = HTML.read_text(encoding="utf-8")
m = re.search(r"const payload\s*=\s*(\{.*?\});\s*\n", source, re.S)
assert m, "HTML const payload not found"
payload = json.loads(m.group(1))
assert payload["word_count"] == 98054
assert payload["indexed_word_count"] == 98011
assert payload["bucket_word_id_bits"] == 32

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    payload_path = td / "payload.json"
    rebuilt = td / "dictionary.bin"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    build(payload_path, rebuilt)
    assert rebuilt.read_bytes() == DICT.read_bytes(), "HTML/native dictionary payload drifted"

print("test_html_dictionary_payload: OK")
