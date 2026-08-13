from pathlib import Path
root = Path(__file__).resolve().parents[1]
files = [root/'App'/'ZYCandidatePanel.mm', root/'App'/'ZYInputController.mm']
text = '\n'.join(p.read_text(encoding='utf-8') for p in files)
assert '/tmp/zhu-yin-mouse.log' not in text
assert 'ZYTraceMouse' not in text
assert 'ZYTraceMouseState' not in text
assert 'ZYTraceMouseController' not in text
# Removing diagnostics must not remove mouse routing itself.
panel = (root/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')
assert '- (void)mouseDown:(NSEvent *)event' in panel
assert '[self.panel candidateViewDidChooseIndex:idx]' in panel
assert '[self.panel candidateViewToggleScript]' in panel
assert '[self.panel candidateViewToggleHelp]' in panel
assert '[self.panel candidateViewRequestClearLearning]' in panel
print('mouse diagnostics removed static: OK')
