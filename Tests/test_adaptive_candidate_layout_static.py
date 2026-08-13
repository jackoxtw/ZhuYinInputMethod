from pathlib import Path

root = Path(__file__).resolve().parents[1]
panel = (root / 'App' / 'ZYCandidatePanel.mm').read_text(encoding='utf-8')
header = (root / 'App' / 'ZYCandidatePanel.h').read_text(encoding='utf-8')
controller = (root / 'App' / 'ZYInputController.mm').read_text(encoding='utf-8')

# The panel must expose its visual column count so keyboard navigation follows the grid.
assert '@property(nonatomic,readonly) NSUInteger columns;' in header
assert '_cv.columns' in panel
assert '_panel.columns' in controller
assert '_selected>=columns?_selected-columns:_selected' in controller
assert 'MIN(_candidateCount-1,_selected+columns)' in controller

# Normal short candidates stay dense, while longer composition candidates get wider cells.
assert 'maxChars<=2?10:(maxChars<=5?5:4)' in panel
assert 'cellW=720.0/self.columns' in panel
assert '_cv.columns=columns' in panel

# Long candidates wrap in their own cell. Never hide candidate text with an ellipsis.
assert 'NSStringDrawingUsesLineFragmentOrigin' in panel
assert 'NSLineBreakByCharWrapping' in panel
assert 'NSRectClip' in panel
assert 'NSLineBreakByTruncatingTail' not in panel
assert '@"…"' not in panel

# Long composition layout uses a readable floor instead of shrinking indefinitely.
assert 'MAX(12.0' in panel or 'fontSize>=12.0' in panel

print('Adaptive candidate layout regression tests: OK')
