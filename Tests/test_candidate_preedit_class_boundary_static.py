from pathlib import Path

src = (Path(__file__).resolve().parents[1] / 'Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')

def implementation_block(name: str) -> str:
    start = src.index(f'@implementation {name}')
    end = src.index('@end', start)
    return src[start:end]

help_block = implementation_block('ZYHelpView')
clear_block = implementation_block('ZYClearLearningView')
candidate_block = implementation_block('ZYCandidateView')

assert 'preeditText' not in help_block, 'ZYHelpView must not reference candidate-only preeditText'
assert 'preeditText' not in clear_block, 'ZYClearLearningView must not reference candidate-only preeditText'
assert '- (CGFloat)preeditHeaderHeight{return self.preeditText.length?ZYPreeditHeaderHeight:0.0;}' in candidate_block
