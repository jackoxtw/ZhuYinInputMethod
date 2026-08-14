from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmake = (ROOT / 'Platforms/Windows/CMakeLists.txt').read_text(encoding='utf-8')
bridge = (ROOT / 'Platforms/Windows/Ime/ZhuyinTextService.cpp').read_text(encoding='utf-8')

assert 'Shared/Core/ZYEngine.c' in cmake
assert '#include "ZYEngine.h"' in (ROOT / 'Platforms/Windows/Ime/ZhuyinTextService.h').read_text(encoding='utf-8')
assert 'InputMethodKit' not in bridge
assert 'lookup(' in bridge and 'commitCandidate(' in bridge and 'reset(' in bridge
print('test_windows_scaffold_static: OK')
