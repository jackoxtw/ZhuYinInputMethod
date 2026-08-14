from pathlib import Path

info = (Path(__file__).resolve().parents[1] / 'App' / 'Info.plist').read_text(encoding='utf-8')
resources = Path(__file__).resolve().parents[1] / 'Resources'
top_level = info.split('<key>ComponentInputModeDict</key>', 1)[0]

assert '<key>CFBundleIdentifier</key><string>tw.zhuyin.inputmethod.v3</string>' in top_level
assert '<key>InputMethodConnectionName</key><string>tw.zhuyin.inputmethod.v3_Connection</string>' in top_level
assert '<key>tsInputMethodIconFileKey</key><string>AppIcon.icns</string>' in top_level
assert '<key>tsInputMethodAlternateIconFileKey</key><string>AppIcon.icns</string>' in top_level
assert '<key>TISInputSourceID</key>\n                <string>tw.zhuyin.inputmethod.v3.zhuyin</string>' in info
for locale in ['zh-Hant.lproj', 'zh_TW.lproj']:
    strings = (resources / locale / 'InfoPlist.strings').read_text(encoding='utf-8')
    assert '"tw.zhuyin.inputmethod.v3.zhuyin" = "逐音輸入法";' in strings

print('input method icon registration static regression: OK')
