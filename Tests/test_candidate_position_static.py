from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms/macOS/App/ZYInputController.mm').read_text('utf-8')
ax = (root / 'Platforms/macOS/App/ZYAccessibilityCaret.mm').read_text('utf-8')
panel = (root / 'Platforms/macOS/App/ZYCandidatePanel.mm').read_text('utf-8')


# InputMethodKit has a dedicated candidate-window positioning API.  Its index is
# relative to the inline session, and it works even when document-access ranges
# are unavailable.  This must be the primary path; mouse location is not a caret.
assert 'attributesForCharacterIndex:' in controller, 'must query IMKTextInput lineHeightRectangle'
assert 'lineHeightRectangle:' in controller, 'must obtain the IMK line-height caret rectangle'
assert 'NSEvent.mouseLocation' not in controller, 'mouse location must never be used as text caret fallback'
assert controller.index('attributesForCharacterIndex:') < controller.index('firstRectForCharacterRange:'), 'IMK lineHeightRectangle must be the primary caret source'
assert 'NSUInteger inlineIndex=0;' in controller, 'IMK lookup must default to relative inline index 0/current selection'
assert 'inlineIndex=marked.length-1;' in controller, 'active inline sessions must use a relative index, never a document-absolute range location'
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
assert 'fitsBelow' in panel and 'fitsAbove' in panel
assert 'NSMinY(rect)' in panel and 'NSMaxY(rect)' in panel

# Horizontal placement must mirror the vertical flip behavior.  When the panel
# does not fit to the right of the caret, it should first try the caret's left
# side before falling back to visible-frame clamping.  This keeps the nearest
# panel corner within the normal 6pt caret gap instead of pinning the panel to
# the screen edge.
assert 'rightX=NSMaxX(rect)+gap' in panel
assert 'leftX=NSMinX(rect)-gap-size.width' in panel
assert 'fitsRight' in panel and 'fitsLeft' in panel
assert 'if(fitsRight)' in panel and 'else if(fitsLeft)' in panel
assert 'belowY=NSMinY(rect)-gap-size.height' in panel
assert 'aboveY=NSMaxY(rect)+gap' in panel
assert 'fitsBelow' in panel and 'fitsAbove' in panel
