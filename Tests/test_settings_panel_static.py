from pathlib import Path

root = Path(__file__).resolve().parents[1]
h = (root / 'Platforms/macOS/App/ZYCandidatePanel.h').read_text(encoding='utf-8')
p = (root / 'Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')
c = (root / 'Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')

# Candidate panel exposes a Settings control instead of a destructive clear-learning button.
assert '- (NSRect)settingsRect' in p
assert '@"設定"' in p
candidate_view_start = p.index('@implementation ZYCandidateView')
candidate_view_end = p.index('@end', candidate_view_start)
candidate_view = p[candidate_view_start:candidate_view_end]
assert 'clearLearningRect' not in candidate_view
assert '@"清除學習"' not in candidate_view
assert 'candidateViewToggleSettings' in candidate_view

# Settings is a separate non-modal auxiliary panel owned by the candidate panel.
assert 'settingsVisible' in h
assert 'toggleSettings' in h
assert 'closeSettings' in h
assert '@interface ZYSettingsPanel : NSPanel' in p
assert '@interface ZYSettingsView : NSView' in p
assert '@"逐音輸入法設定"' in p
assert '@"學習資料"' in p
assert '@"清除學習資料"' in p

# Clear learning can only be requested from the settings view, and still uses the existing confirmation path.
settings_start = p.index('@implementation ZYSettingsView')
settings_end = p.index('@end', settings_start)
settings_view = p[settings_start:settings_end]
assert 'candidateViewRequestClearLearning' in settings_view
assert 'showClearLearningConfirmation' in c
assert 'ZYRuntimeClearLearning()' in c

# Escape closes Settings before touching composition state.
esc = c[c.index('case 53:'):c.index('case 49:')]
assert 'settingsVisible' in esc
assert 'closeSettings' in esc

# Hiding the candidate panel also releases Settings resources.
order_out = p[p.index('- (void)orderOut:'):p.index('- (void)showNearRect:', p.index('- (void)orderOut:'))]
assert '[self closeSettings]' in order_out

print('settings panel static: OK')
