from pathlib import Path
root = Path(__file__).resolve().parents[1]
c = (root/'Platforms'/'macOS'/'App'/'ZYInputController.mm').read_text(encoding='utf-8')
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')

# Controller must schedule a delayed release instead of keeping a hidden panel forever.
assert '_panelReleaseGeneration' in c
assert '_panelReleaseScheduled' in c
assert '- (void)hideCandidatePanel' in c
assert '2.0*NSEC_PER_SEC' in c or '2*NSEC_PER_SEC' in c
assert 'dispatch_after' in c
assert '__weak ZYInputController *weakSelf=self' in c

# Reusing/showing the candidate panel must cancel any pending release.
ensure_start = c.find('- (ZYCandidatePanel *)ensureCandidatePanel')
ensure_end = c.find('- (void)releaseCandidatePanel', ensure_start)
ensure = c[ensure_start:ensure_end]
assert '_panelReleaseScheduled=NO' in ensure
assert '_panelReleaseGeneration++' in ensure

# Hiding should immediately clear transient candidate strings but must not shrink the backing store;
# the existing delayed release closes it after the idle timeout.
order_start = p.find('- (void)orderOut:(id)sender')
order_end = p.find('- (void)showNearRect:', order_start)
order = p[order_start:order_end]
assert '_cv.words=@[]' in order
assert '_cv.modeLabel=@""' in order
assert '_cv.preeditText=@""' in order
assert '_cv.count=0' in order
assert '_cv.columns=10' in order
assert '_cv.rowHeight=38' in order
assert '_cv.rows=2' in order
assert '[self resizeForRows:2]' not in order

# Normal hide sites should use the delayed lifecycle helper, not bare orderOut.
assert 'if(!_chinese||(!_candidateCount&&!_composition.length)){[self hideCandidatePanel];return;}' in c
print('candidate idle release static: OK')
