from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')
panel = (root / 'Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')

# Preference must be persistent and default-safe (missing bool key == NO => safe mode).
assert 'ZYQuickEnterConfirmKey' in controller, 'controller must define a persistent quick-confirm preference key'
assert '@"ZYQuickEnterConfirm"' in controller, 'quick-confirm preference must use a stable NSUserDefaults key'
assert 'boolForKey:ZYQuickEnterConfirmKey' in controller, 'Return path must read the persisted quick-confirm preference'

# Fast mode: the Enter that selects the final candidate also commits staged Chinese,
# while consumeReturnWhileComposing still returns YES so the web app never sees that Enter.
start = controller.index('- (BOOL)consumeReturnWhileComposing:(id)client')
end = controller.index('\n- (void)refreshCandidates:', start)
enter = controller[start:end]
assert '[self chooseSelected:client]' in enter, 'Return must still select only the highlighted candidate'
assert '_composition.length==0' in enter or '!_composition.length' in enter, 'quick commit must happen only after all Zhuyin is resolved'
assert '_pieceCount' in enter and '[self learnAndCommit:client]' in enter, 'quick mode must commit staged Chinese after the final selection'
assert 'return YES;' in enter, 'the final-selection Enter must remain consumed by the IME'

# Settings UI must expose both modes and persist the selection.
assert '@"瀏覽器安全模式"' in panel, 'settings must expose browser-safe mode'
assert '@"快速確認模式"' in panel, 'settings must expose quick-confirm mode'
assert '@"ZYQuickEnterConfirm"' in panel, 'settings and controller must share the same persisted key'
assert 'setBool:' in panel and 'ZYQuickEnterConfirmKey' in panel, 'clicking a mode must persist it'

print('test_quick_enter_confirm_mode_static: OK')
