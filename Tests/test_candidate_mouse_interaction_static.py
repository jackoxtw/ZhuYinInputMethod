from pathlib import Path
p = Path('Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')
view_start = p.find('@implementation ZYCandidateView')
draw_start = p.find('- (void)drawRect:', view_start)
view_head = p[view_start:draw_start]
panel_start = p.find('@implementation ZYCandidatePanel')
panel_init_end = p.find('- (NSUInteger)columns', panel_start)
panel_head = p[panel_start:panel_init_end]
assert '- (BOOL)acceptsFirstMouse:(NSEvent *)event' in view_head, 'candidate view must accept click-through mouse down'
assert 'return YES;' in view_head[view_head.find('- (BOOL)acceptsFirstMouse:(NSEvent *)event'):], 'acceptsFirstMouse must return YES'
assert '- (BOOL)needsPanelToBecomeKey{return NO;}' in view_head, 'candidate view must not require keyboard focus'
assert '- (BOOL)acceptsFirstResponder{return NO;}' in view_head, 'candidate view must not become first responder'
assert '- (BOOL)mouseDownCanMoveWindow{return NO;}' in view_head, 'candidate clicks must not be treated as window dragging'
assert '- (BOOL)canBecomeKeyWindow{return YES;}' in panel_head, 'nonactivating panel must be key-capable so AppKit can route clicks'
assert '- (BOOL)canBecomeMainWindow{return NO;}' in panel_head, 'candidate panel must never become main window'
assert 'self.becomesKeyOnlyIfNeeded=YES;' in panel_head, 'panel must only become key if a hit view needs keyboard focus'
assert 'self.ignoresMouseEvents=NO;' in panel_head, 'candidate panel must explicitly accept mouse events'
print('candidate mouse interaction static: OK')
