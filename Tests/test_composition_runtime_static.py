from pathlib import Path

s = (Path(__file__).resolve().parents[1] / 'Platforms' / 'macOS' / 'App' / 'ZYRuntime.mm').read_text()
assert '#include "ZYComposer.h"' in s
assert 'zy_composer_lookup_with_workspace(&gEngine,query' in s
assert 'segment_count' in s
assert 'segment_ids' in s
assert 'segment_consume_codepoints' in s
assert 'zy_learning_word_frequency_bonus(&gLearning,sid)' in s
assert 'zy_learning_word_recency_bonus(&gLearning,sid)' in s
assert 'ZYRuntimeCandidateWord' in s

# Composition ranking must preserve composer quality and cap learning by
# category so extra segmentation cannot accumulate an automatic advantage.
assert 'ZY_COMPOSITION_LEARN_FREQUENCY_CAP' in s
assert 'ZY_COMPOSITION_LEARN_RECENCY_CAP' in s
assert 'ZY_COMPOSITION_LEARN_QUERY_CAP' in s
assert 'ZY_COMPOSITION_LEARN_PREFERENCE_CAP' in s
assert 'c.score/20' not in s and 'c.score / 20' not in s
assert 'best_composed_score' in s
assert 'ZY_COMPOSITION_COMPLETE_QUALITY_WINDOW = 8000' in s
assert 'ZY_COMPOSITION_PARTIAL_QUALITY_WINDOW = 60000' in s
assert 'c.word_complete?ZY_COMPOSITION_COMPLETE_QUALITY_WINDOW:ZY_COMPOSITION_PARTIAL_QUALITY_WINDOW' in s

print('test_composition_runtime_static: OK')
