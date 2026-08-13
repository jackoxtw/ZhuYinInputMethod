from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
build = (ROOT/'build_and_install.command').read_text()
cmake = (ROOT/'CMakeLists.txt').read_text()
assert 'for f in ZYDictionary ZYEngine ZYComposer ZYLearning ZYConversion' in build
assert 'Core/ZYComposer.c' in cmake
print('test_composition_build_static: OK')
