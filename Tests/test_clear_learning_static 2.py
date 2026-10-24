from pathlib import Path
root = Path(__file__).resolve().parents[1]
h = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.h').read_text()
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text()
c = (root/'Platforms'/'macOS'/'App'/'ZYInputController.mm').read_text()
rh = (root/'Platforms'/'macOS'/'App'/'ZYRuntime.h').read_text()
r = (root/'Platforms'/'macOS'/'App'/'ZYRuntime.mm').read_text()

assert 'candidatePanelRequestClearLearning' in h
assert '@"清除學習"' in p
assert 'clearLearningRect' in p
assert 'MAX(110.0' in p
assert 'candidatePanelRequestClearLearning' in c
assert '確定要清除學習資料嗎？' in p
assert '@"取消"' in p
assert '@"清除學習資料"' in p
assert 'runModal' not in c
assert 'showClearLearningConfirmation' in c
assert 'candidatePanelConfirmClearLearning' in c
assert 'ZYRuntimeClearLearning()' in c
assert 'if(ok&&_composition.length)[self refreshCandidates:[self client]]' in c
assert 'ZYRuntimeClearLearning' in rh
assert 'learning_A.dat' in r and 'learning_B.dat' in r and '@"_A.dat"' in r and '@"_B.dat"' in r
assert 'zy_learning_reset(&gLearning' in r
# Safety: clearing only happens in the explicit confirmation callback.
assert c.index('candidatePanelRequestClearLearning') < c.index('candidatePanelConfirmClearLearning')
print('test_clear_learning_static: OK')
