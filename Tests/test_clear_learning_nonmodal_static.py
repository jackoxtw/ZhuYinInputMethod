from pathlib import Path
root = Path(__file__).resolve().parents[1]
h = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.h').read_text(encoding='utf-8')
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')
c = (root/'Platforms'/'macOS'/'App'/'ZYInputController.mm').read_text(encoding='utf-8')

# Background input methods must never enter a hidden modal NSAlert for this action.
clear = c[c.find('- (void)candidatePanelRequestClearLearning'):c.find('- (NSMenu *)menu')]
assert 'runModal' not in clear
assert 'NSAlert' not in clear

# The candidate panel owns a visible, non-modal confirmation surface.
assert 'clearLearningConfirmationVisible' in h
assert 'showClearLearningConfirmation' in h
assert 'closeClearLearningConfirmation' in h
assert 'showClearLearningResult:' in h
assert 'candidatePanelConfirmClearLearning' in h
assert '@interface ZYClearLearningPanel : NSPanel' in p
assert 'NSWindowStyleMaskNonactivatingPanel' in p
assert 'NSStatusWindowLevel+1' in p
assert 'orderFrontRegardless' in p
assert '確定要清除學習資料嗎？' in p
assert '@"取消"' in p
assert '@"清除學習資料"' in p

# Clear happens only after the custom confirmation calls back into the controller.
assert '- (void)candidatePanelConfirmClearLearning' in c
confirm = c[c.find('- (void)candidatePanelConfirmClearLearning'):c.find('- (NSMenu *)menu')]
assert 'ZYRuntimeClearLearning()' in confirm
assert 'showClearLearningResult:ok' in confirm

# Esc dismisses the confirmation before touching composition state.
esc = c[c.find('case 53:'):c.find('case 49:')]
assert 'clearLearningConfirmationVisible' in esc
assert 'closeClearLearningConfirmation' in esc
print('test_clear_learning_nonmodal_static: OK')
