#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
engine = (ROOT / "Core" / "ZYEngine.c").read_text()
runtime = (ROOT / "App" / "ZYRuntime.mm").read_text()

assert "m.initials>0&&m.matched>=5&&m.remaining==0" in engine
assert "codepoints(c.word,strlen(c.word))>=5" in engine
assert "ZYCandidate raw[256]" in runtime
assert "zy_engine_lookup(&gEngine,query,raw,256)" in runtime
assert "if(learned_preference>raw[i].preference_rank)" in runtime
assert "size_t n=rn<128?rn:128" in runtime
print("test_brand_recall_static: OK")
