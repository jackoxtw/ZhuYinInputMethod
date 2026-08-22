from pathlib import Path

p = Path('Platforms/macOS/App/ZYCandidatePanel.mm')
s = p.read_text(encoding='utf-8')
impl = '- (CGFloat)preeditHeaderHeight{return (self.preeditText.length||self.zhuyinText.length)?ZYPreeditHeaderHeight:0.0;}'
assert s.count(impl) == 1, f'preeditHeaderHeight must be implemented only once in ZYCandidateView, found {s.count(impl)}'
start = s.index('@implementation ZYCandidateView')
end = s.index('@end', start)
assert impl in s[start:end], 'preeditHeaderHeight must belong to ZYCandidateView'
