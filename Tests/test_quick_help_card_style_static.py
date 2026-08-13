from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = (root/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')

assert '@interface ZYHelpView : NSView' in p
assert '- (BOOL)acceptsFirstMouse:(NSEvent *)event' in p
assert '- (BOOL)needsPanelToBecomeKey{return NO;}' in p
assert '- (BOOL)acceptsFirstResponder{return NO;}' in p
assert '- (BOOL)mouseDownCanMoveWindow{return NO;}' in p
assert '快速使用說明' in p
assert '@"關閉"' in p
assert '@"×"' in p
assert 'helpCloseRect' in p
assert 'helpBottomCloseRect' in p
assert 'NSStatusWindowLevel+1' in p
assert '[_helpPanel orderFrontRegardless]' in p
assert 'NSBezierPath bezierPathWithRoundedRect:self.bounds xRadius:12 yRadius:12' in p
assert '[self.owner closeQuickHelp]' in p
assert 'NSTextField *label=[NSTextField labelWithString:' not in p
print('test_quick_help_card_style_static: OK')
assert 'Shift + A–Z' in p
assert '無候選：Caps Lock 關小寫／開大寫' in p
assert 'initWithContentRect:NSMakeRect(0,0,440,460)' in p
