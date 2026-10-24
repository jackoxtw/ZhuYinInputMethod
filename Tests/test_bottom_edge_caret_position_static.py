from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms/macOS/App/ZYInputController.mm').read_text('utf-8')

start = controller.index('- (NSRect)clientRect:(id)client')
end = controller.index('- (id)composedString:', start)
body = controller[start:end]

# IMKTextInput attributesForCharacterIndex uses an index relative to the current
# inline session.  With no inline session, 0 means the current selection.
# Never feed document-absolute selectedRange / markedRange locations into it.
assert 'NSUInteger inlineIndex=0;' in body
assert 'inlineIndex=marked.length-1;' in body
assert 'attributesForCharacterIndex:inlineIndex' in body
assert 'cursor=(NSInteger)NSMaxRange(marked)-1' not in body
assert 'cursor=(NSInteger)selected.location' not in body

# A failed caret query must never fabricate a caret in the middle of the screen.
assert 'NSMidX(vis)' not in body
assert 'NSMidY(vis)' not in body
assert 'return NSZeroRect;' in body

# The popup caller must only move the panel when a real caret rectangle exists;
# otherwise an already-visible panel keeps its previous real position.
refresh_start = controller.index('- (void)refreshPanel:(id)client')
refresh_end = controller.index('- (void)openSpecialCandidates:', refresh_start)
refresh = controller[refresh_start:refresh_end]
assert 'NSRect caret=[self clientRect:client];' in refresh
assert 'if(ZYUsableCaretRect(caret))' in refresh
assert '[panel showNearRect:caret];' in refresh
