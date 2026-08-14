from pathlib import Path
root=Path(__file__).resolve().parents[1]
headers=[
    root/'Shared/Core/ZYDictionary.h',
    root/'Shared/Core/ZYEngine.h',
    root/'Shared/Core/ZYLearning.h',
    root/'Shared/Core/ZYConversion.h',
    root/'Platforms/macOS/App/ZYRuntime.h',
]
for p in headers:
    s=p.read_text(encoding='utf-8')
    assert '#ifdef __cplusplus' in s, f'{p.name}: missing __cplusplus guard'
    assert 'extern "C" {' in s, f'{p.name}: missing extern C block'
print('cpp linkage header test passed')
