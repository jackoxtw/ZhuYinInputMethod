from pathlib import Path
root=Path(__file__).resolve().parents[1]
headers=[
    root/'Core/ZYDictionary.h',
    root/'Core/ZYEngine.h',
    root/'Core/ZYLearning.h',
    root/'Core/ZYConversion.h',
    root/'App/ZYRuntime.h',
]
for p in headers:
    s=p.read_text(encoding='utf-8')
    assert '#ifdef __cplusplus' in s, f'{p.name}: missing __cplusplus guard'
    assert 'extern "C" {' in s, f'{p.name}: missing extern C block'
print('cpp linkage header test passed')
