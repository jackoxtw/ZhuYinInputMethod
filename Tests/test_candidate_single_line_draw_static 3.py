from pathlib import Path

panel = (Path(__file__).resolve().parents[1] / 'Platforms' / 'macOS' / 'App' / 'ZYCandidatePanel.mm').read_text(encoding='utf-8')
candidate = panel.split('@implementation ZYCandidateView', 1)[1]
draw = candidate.split('- (void)drawRect:', 1)[1].split('- (void)mouseDown:', 1)[0]

# Short (10-column) and medium (5-column) candidates are explicitly prepared
# as single lines.  They must use the lightweight point drawing path instead of
# creating a multiline NSString drawing layout per cell on every keypress.
assert 'if(self.columns==4)' in draw
assert '[w drawWithRect:textRect' in draw
assert '[w drawAtPoint:textOrigin withAttributes:attrs]' in draw
single_line = draw.split('if(self.columns==4)', 1)[1].split('[NSGraphicsContext restoreGraphicsState]', 1)[0]
assert '[w sizeWithAttributes:attrs]' not in single_line

print('candidate single-line drawing static regression: OK')
