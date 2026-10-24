from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
plist=(ROOT/'Platforms/macOS/App/Info.plist').read_text(encoding='utf-8')
main=(ROOT/'Platforms/macOS/App/main.m').read_text(encoding='utf-8')

assert '<key>LSBackgroundOnly</key><false/>' in plist
assert '<key>LSUIElement</key><true/>' in plist
assert 'NSApplicationActivationPolicyAccessory' in main
assert '<key>InputMethodConnectionName</key><string>tw.zhuyin.inputmethod.v3_Connection</string>' in plist
print('test_return_guard_agent_mode_static: OK')
