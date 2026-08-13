from pathlib import Path

root = Path(__file__).resolve().parents[1]
runtime = (root / "App" / "ZYRuntime.mm").read_text()
compact = "".join(runtime.split())

assert "zy_engine_lookup(&gEngine,query,raw,256)" in runtime, \
    "Runtime must recall 256 raw dictionary candidates before applying learning"
assert "size_tn=rn<128?rn:128;" in compact, \
    "Runtime must trim the learned raw pool back to 128 before composition"
assert "zy_learning_word_count(&gLearning,raw[i].id)" in runtime, \
    "Runtime must inspect whether a dictionary word was learned"
assert "raw[i].dictionary_exact" in runtime and "raw[i].matched_chars>1" in runtime, \
    "Learned multi-syllable exact abbreviation matches need a soft recall preference"
assert "raw[i].preference_rank<1" in runtime and "raw[i].preference_rank=1" in compact, \
    "Learned exact abbreviation recall must assign soft preference rank 1"
assert "final_syllable_partial" in runtime, \
    "Runtime must recognize a learned word whose last syllable is still being typed"
assert "(raw[i].dictionary_exact||raw[i].final_syllable_partial)" in compact, \
    "Soft learned-word recall must cover exact and final-syllable-partial matches"
print("test_learned_abbreviation_recall_static: OK")
