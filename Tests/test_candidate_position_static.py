from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'App/ZYInputController.mm').read_text('utf-8')
ax = (root / 'App/ZYAccessibilityCaret.mm').read_text('utf-8')
panel = (root / 'App/ZYCandidatePanel.mm').read_text('utf-8')


# InputMethodKit has a dedicated candidate-window positioning API.  Its index is
# relative to the inline session, and it works even when document-access ranges
# are unavailable.  This must be the primary path; mouse location is not a caret.
assert 'attributesForCharacterIndex:' in controller, 'must query IMKTextInput lineHeightRectangle'
assert 'lineHeightRectangle:' in controller, 'must obtain the IMK line-height caret rectangle'
assert 'NSEvent.mouseLocation' not in controller, 'mouse location must never be used as text caret fallback'
assert controller.index('attributesForCharacterIndex:') < controller.index('firstRectForCharacterRange:'), 'IMK lineHeightRectangle must be the primary caret source'
assert 'if(cursor>0) cursor--;' in controller, 'end-of-inline-session lookup must step onto the last real character'
assert 'for(;cursor>=0;cursor--)' not in controller, 'caret lookup must not scan backward through preedit characters'
assert '@autoreleasepool' in controller[controller.index('- (NSRect)clientRect:(id)client'):controller.index('- (void)updateMarked:')], 'caret lookup should release temporary AppKit objects promptly'
assert '!(fabs(rect.origin.x)<0.5 && fabs(rect.origin.y)<0.5)' in controller, 'a synthetic (0,0) rect must not be accepted as a real caret'
assert '/tmp/zhu-yin-caret.log' not in controller, 'caret diagnostic logging should be removed after positioning was verified'
assert 'ZYTraceCaret' not in controller, 'caret tracing helper should not remain in production input path'

# A legal insertion caret returned by NSTextInputClient / AX can be zero-width.
# Rejecting it as an "empty rect" is the regression that forced the panel to fallback.
assert 'NSIsEmptyRect(ax)' not in controller, 'AX caret must allow zero-width rects'
assert 'NSIsEmptyRect(rect)' not in controller, 'IMK caret must allow zero-width rects'
assert 'CGRectIsEmpty(bounds)' not in ax, 'AX bounds must allow zero-width insertion carets'

# A zero-width caret does not geometrically intersect a screen rectangle reliably;
# screen selection must use the caret anchor point instead.
assert 'NSIntersectsRect(s.frame,rect)' not in panel
assert 'NSPointInRect' in panel

# Candidate panel should keep its normal size (subject only to visible-frame maximum),
# anchor to the caret, and flip vertically when the lower side has no room.
assert 'placeBelow' in panel
assert 'NSMinY(rect)' in panel and 'NSMaxY(rect)' in panel
