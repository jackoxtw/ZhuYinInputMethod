from pathlib import Path

app = Path(__file__).resolve().parents[1] / 'Release' / '逐音輸入法-v0.1.47' / '逐音輸入法.app'
info = (app / 'Contents' / 'Info.plist').read_text(encoding='utf-8')
top_level = info.split('<key>ComponentInputModeDict</key>', 1)[0]

assert '<key>CFBundleIconFile</key><string>AppIcon.icns</string>' in info
assert '<key>tsInputMethodIconFileKey</key><string>AppIcon.icns</string>' in top_level
assert (app / 'Contents' / 'Resources' / 'AppIcon.icns').is_file()

print('release app icon: OK')
