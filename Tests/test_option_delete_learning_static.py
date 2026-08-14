from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'App' / 'ZYInputController.mm').read_text(encoding='utf-8')
panel = (root / 'App' / 'ZYCandidatePanel.mm').read_text(encoding='utf-8')
runtime_h = (root / 'App' / 'ZYRuntime.h').read_text(encoding='utf-8')
learning_h = (root / 'Core' / 'ZYLearning.h').read_text(encoding='utf-8')

assert 'ZYRuntimeRemoveCandidateLearning' in runtime_h
assert 'zy_learning_remove_word' in learning_h
assert 'candidatePanelDidDeleteIndex:' in controller
assert 'NSEventModifierFlagOption' in controller
assert '刪除' in panel
print('option delete learning static: OK')
