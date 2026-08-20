from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')

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
assert '先送出中文，再輸入英文' in p
assert 'initWithContentRect:NSMakeRect(0,0,440,460)' in p
assert 'github.com/jackoxtw/ZhuYinInputMethod' in p
assert '- (NSRect)githubRect' in p
assert 'NSPointInRect(p,self.githubRect)' in p
assert '[[NSWorkspace sharedWorkspace] openURL:' in p
assert 'https://github.com/jackoxtw/ZhuYinInputMethod' in p
assert '- (NSRect)scriptRect{return NSMakeRect(732,6,48,32);}' in p
assert '- (NSRect)helpRect{return NSMakeRect(732,42,48,18);}' in p
assert 'drawAtPoint:NSMakePoint(756-modeSize.width/2,66)' in p
