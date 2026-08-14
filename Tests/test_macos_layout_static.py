from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

assert (ROOT / 'Platforms/macOS/App/ZYInputController.mm').is_file()
assert (ROOT / 'Platforms/macOS/Packaging/安裝逐音輸入法.command').is_file()
launcher = (ROOT / 'build_and_install.command').read_text(encoding='utf-8')
assert 'Platforms/macOS/scripts/build_and_install.command' in launcher
print('test_macos_layout_static: OK')
