from pathlib import Path

panel = (Path(__file__).resolve().parents[1] / 'Platforms' / 'macOS' / 'App' / 'ZYCandidatePanel.mm').read_text(encoding='utf-8')
start = panel.index('static NSDictionary *ZYCandidateTextAttributes')
end = panel.index('static NSDictionary *ZYModeLabelAttributes', start)
cache = panel[start:end]

# A single candidate size must not eagerly instantiate every system font size
# (12 through 18) on the first phonetic completion.
assert 'for(NSInteger size=12;size<=18;size++)' not in cache
assert 'attrs[index]' in cache

print('candidate font cache static regression: OK')
