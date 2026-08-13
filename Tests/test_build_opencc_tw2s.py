#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
s = (ROOT / "build_and_install.command").read_text("utf-8")

required = [
    'OPENCC_TAG="ver.1.3.1"',
    'TSCharacters.txt',
    'TSPhrases.txt',
    'TWVariants.txt',
    'TWVariantsRevPhrases.txt',
    'Tools/build_tw2s_opencc.py',
    '--require-full',
    'T2S_FOR_BUILD="$PWD/Resources/t2s.bin"',
    'cp "$T2S_FOR_BUILD" "$RES/t2s.bin"',
]
for token in required:
    assert token in s, token

# The complete build must happen before the selected runtime binary is copied.
assert s.index('Tools/build_tw2s_opencc.py') < s.index('cp "$T2S_FOR_BUILD" "$RES/t2s.bin"')
# Never copy the stale bundled file unconditionally after selecting the full build.
assert 'cp Resources/t2s.bin "$RES/t2s.bin"' not in s
print("test_build_opencc_tw2s: OK")
