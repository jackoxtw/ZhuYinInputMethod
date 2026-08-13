from pathlib import Path

panel = Path('App/ZYCandidatePanel.mm').read_text(encoding='utf-8')

resize = panel.split('- (void)resizeForRows:', 1)[1].split('- (void)updateWords:', 1)[0]
assert 'desiredHeight' in resize, 'resize policy should name the required/desired height explicitly'
assert 'self.isVisible' in resize, 'resize policy must distinguish active composition from hidden/new composition'
assert 'MAX(current.height,desiredHeight)' in resize.replace(' ', ''), \
    'visible panel must be grow-only so it cannot shrink during one composition'

order_out = panel.split('- (void)orderOut:(id)sender{', 1)[1].split('- (void)showNearRect:', 1)[0]
assert 'resizeForRows:' not in order_out, 'hiding the panel must not shrink/reallocate its backing store'

print('candidate grow-only panel checks: OK')
