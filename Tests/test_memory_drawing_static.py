from pathlib import Path
p = Path('Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')
start = p.find('@implementation ZYCandidateView')
end = p.find('@end', start)
view = p[start:end]
# Common paragraph style and immutable label/font attributes should be cached.
assert 'ZYSharedCandidateParagraphStyle()' in view
assert 'ZYShortcutLabelAttributes()' in view
assert 'ZYCandidateShortcuts()' in view
assert 'ZYCandidateTextAttributes(' in view
assert 'ZYModeLabelAttributes()' in view
assert 'ZYHelpLabelAttributes()' in view
assert 'ZYClearLearningLabelAttributes()' in view
loop = view[view.find('for(NSUInteger i=0;'):view.find('if(self.modeLabel.length)')]
assert '[[NSMutableParagraphStyle alloc]init]' not in loop
assert '@{NSFontAttributeName:[NSFont systemFontOfSize:9 weight:NSFontWeightBold]' not in loop
# Candidate cells must not allocate a fresh font dictionary on every measurement pass.
assert '@{NSFontAttributeName:[NSFont systemFontOfSize:fontSize' not in loop
print('memory drawing static: OK')
