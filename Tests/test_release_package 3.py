from pathlib import Path
import zipfile


root = Path(__file__).resolve().parents[1]
archive = root / 'Release' / '逐音輸入法-v0.1.48.zip'
assert archive.is_file(), 'missing v0.1.48 release ZIP'

with zipfile.ZipFile(archive) as package:
    names = set(package.namelist())

assert any(name.endswith('/Contents/Info.plist') for name in names)
assert any(name.endswith('.command') for name in names)
assert any(name.endswith('.txt') for name in names)
assert not any(name.startswith('__MACOSX/') for name in names)

print('release package: OK')
