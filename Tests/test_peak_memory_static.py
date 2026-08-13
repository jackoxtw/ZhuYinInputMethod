from pathlib import Path

panel = Path('App/ZYCandidatePanel.mm').read_text()
controller = Path('App/ZYInputController.mm').read_text()
runtime = Path('App/ZYRuntime.mm').read_text()

# Candidate drawing should use layout prepared during candidate updates instead
# of repeatedly measuring strings inside drawRect.
draw = panel.split('- (void)drawRect:(NSRect)dirty{', 3)[-1]
draw = draw.split('- (void)mouseDown:', 1)[0]
assert 'boundingRectWithSize' not in draw, 'candidate drawRect must not measure candidate text'
assert 'prepareCandidateTextLayout' in panel, 'candidate text layout must be prepared outside drawRect'
assert 'textFontSizes' in panel and 'textVerticalOffsets' in panel
assert 'boundingRectWithSize' not in panel, 'candidate panel must not measure candidate text'

# Resize/front operations should be conditional so stable typing does not keep
# asking AppKit to recreate backing surfaces or reorder an already-visible panel.
resize = panel.split('- (void)resizeForRows:', 1)[1].split('- (void)updateWords:', 1)[0]
assert 'NSEqualSizes' in resize or 'fabs(' in resize
assert 'self.contentSize' not in resize, 'NSWindow has no readable contentSize property getter'
assert 'self.contentView.bounds.size' in resize, 'compare against the content view size before setContentSize:'
show = panel.split('- (void)showNearRect:', 1)[1]
assert 'NSEqualRects' in show or 'fabs(' in show
assert 'if(!self.isVisible)' in show

# Short-lived Objective-C objects generated during lookup/layout should be
# drained at a local boundary instead of waiting for a later run-loop pool.
assert '@autoreleasepool' in runtime, 'runtime lookup needs a local autorelease pool'
assert '@autoreleasepool' in panel, 'candidate layout preparation needs a local autorelease pool'

# Updating marked text constructs the preedit string for every key event. Its
# temporary Objective-C objects must drain before the next input event rather
# than accumulating in InputMethodKit's outer event pool.
marked = controller.split('- (void)updateMarked:(id)client {', 1)[1].split('- (void)refreshCandidates:(id)client', 1)[0]
assert '@autoreleasepool' in marked, 'marked-text update needs a local autorelease pool'

# The old caret diagnostic must be gone too.
assert '/tmp/zhu-yin-caret.log' not in controller
assert 'ZYTraceCaret' not in controller

print('peak-memory static checks: OK')
