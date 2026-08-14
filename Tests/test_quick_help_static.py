from pathlib import Path
root = Path(__file__).resolve().parents[1]
h = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.h').read_text()
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text()
c = (root/'Platforms'/'macOS'/'App'/'ZYInputController.mm').read_text()

assert 'candidatePanelToggleHelp' in h
assert 'quickHelpVisible' in h
assert 'toggleQuickHelp' in h
assert 'closeQuickHelp' in h
assert '@interface ZYHelpPanel : NSPanel' in p
assert '- (BOOL)canBecomeKeyWindow{return YES;}' in p
assert '- (BOOL)canBecomeMainWindow{return NO;}' in p
assert 'NSWindowStyleMaskNonactivatingPanel' in p
assert 'if(!_helpPanel)' in p
assert '@interface ZYHelpView : NSView' in p
assert '[_helpPanel orderFrontRegardless]' in p
assert '@"說明"' in p
assert 'helpRect' in p
assert 'MAX(110.0' in p
assert 'if(_panel.quickHelpVisible)' in c
assert '[_panel closeQuickHelp]' in c
assert 'candidatePanelToggleHelp' in c
print('test_quick_help_static: OK')
