from pathlib import Path

src = Path('Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')

# A release build must not synchronize user defaults or keep alternate
# diagnostic branches in its per-key refresh path.  Those branches were useful
# to identify the peak, but both CFPreferences synchronization and their
# temporary UI paths add work and allocations to normal input.
for forbidden in [
    'MemoryDiagnosticMode',
    'currentMemoryDiagnosticMode',
    'CFPreferencesAppSynchronize',
    'CFPreferencesCopyAppValue',
    'prepareCandidatePanelWithoutShowing',
    'showBlankDiagnosticPanelNearRect',
]:
    assert forbidden not in src, f'release input path must not retain diagnostic code: {forbidden}'

refresh_start = src.index('- (void)refreshCandidates:(id)client')
refresh_end = src.index('- (void)refreshPanel:(id)client', refresh_start)
refresh = src[refresh_start:refresh_end]
assert 'ZYRuntimeLookup' in refresh
assert '[self refreshPanel:client]' in refresh

print('release memory diagnostic removal static regression test: OK')
