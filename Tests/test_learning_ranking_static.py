from pathlib import Path

root = Path(__file__).resolve().parents[1]
engine_h = (root / 'Core/ZYEngine.h').read_text(encoding='utf-8')
engine_c = (root / 'Core/ZYEngine.c').read_text(encoding='utf-8')
learning_h = (root / 'Core/ZYLearning.h').read_text(encoding='utf-8')
learning_c = (root / 'Core/ZYLearning.c').read_text(encoding='utf-8')
runtime_h = (root / 'App/ZYRuntime.h').read_text(encoding='utf-8')
runtime = (root / 'App/ZYRuntime.mm').read_text(encoding='utf-8')
controller = (root / 'App/ZYInputController.mm').read_text(encoding='utf-8')

# Candidate preference is a rank, not a permanent boolean bonus.
assert 'preference_rank' in engine_h
assert 'query_preferred' not in engine_h
assert 'if(a->preference_rank!=b->preference_rank)' in engine_c.replace(' ', '')

# Core must expose explicit event and bounded adaptive scoring APIs.
for token in [
    'ZY_LEARN_WORD_FREQ_CAP 31',
    'ZY_LEARN_QUERY_FREQ_CAP 8',
    'ZY_LEARN_PHRASE_FREQ_CAP 16',
    'ZY_LEARN_WORD_RECENCY_EVENTS 30',
    'ZY_LEARN_QUERY_PREFERRED_EVENTS 64',
    'ZY_LEARN_PHRASE_RECENCY_EVENTS 32',
    'zy_learning_begin_event',
    'zy_learning_word_frequency_bonus',
    'zy_learning_word_recency_bonus',
    'zy_learning_query_preference_rank',
    'zy_learning_phrase_frequency_bonus',
    'zy_learning_phrase_recency_bonus',
]:
    assert token in learning_h, token

# Persisted layout stays version-1 compatible: no new persistent fields.
assert 'typedef struct {\n    uint32_t clock;' in learning_h
assert 'ZY_LEARN_MAGIC "ZYLEARN1"' in learning_c
assert 'h.version!=1' in learning_c

# Runtime applies rank 2 only to a live explicit query choice; exact learned
# phrases use rank 1, and ordinary score receives capped adaptive bonuses.
compact_runtime = runtime.replace(' ', '')
assert 'learned_preference=zy_learning_query_preference_rank' in compact_runtime
assert 'if(learned_preference>raw[i].preference_rank)raw[i].preference_rank=learned_preference' in compact_runtime
assert 'c.preference_rank=exact?1:0' in compact_runtime
assert 'zy_learning_word_frequency_bonus' in runtime
assert 'zy_learning_word_recency_bonus' in runtime
assert 'zy_learning_phrase_frequency_bonus' in runtime
assert 'zy_learning_phrase_recency_bonus' in runtime

# Exactly one event boundary is opened by final commit. Highlight movement does
# not learn, and selecting an existing learned phrase refreshes its recency.
assert 'void ZYRuntimeBeginLearningEvent(void);' in runtime_h
assert controller.count('ZYRuntimeBeginLearningEvent();') == 1
learn_commit = controller[controller.index('- (void)learnAndCommit:'):controller.index('- (void)toggleLanguage:')]
assert 'ZYRuntimeBeginLearningEvent();' in learn_commit
assert 'ZYRuntimeLearnPhrase(p->text,p->query,p->pron)' in learn_commit.replace(' ', '')
assert 'ZYRuntimeLearnWord(p->candidateID,p->query)' in learn_commit.replace(' ', '')

print('test_learning_ranking_static: OK')
