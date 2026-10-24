from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms' / 'macOS' / 'App' / 'ZYInputController.mm').read_text(encoding='utf-8')
panel = (root / 'Platforms' / 'macOS' / 'App' / 'ZYCandidatePanel.mm').read_text(encoding='utf-8')
runtime_h = (root / 'Platforms' / 'macOS' / 'App' / 'ZYRuntime.h').read_text(encoding='utf-8')
learning_h = (root / 'Shared' / 'Core' / 'ZYLearning.h').read_text(encoding='utf-8')

assert 'ZYRuntimeRemoveCandidateLearning' in runtime_h
assert 'zy_learning_remove_word' in learning_h
assert 'candidatePanelDidDeleteIndex:' in controller
assert 'NSEventModifierFlagOption' in controller
assert '刪除' in panel
print('option delete learning static: OK')
