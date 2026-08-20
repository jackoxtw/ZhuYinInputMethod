from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
runner = (ROOT / 'run_core_tests.sh').read_text(encoding='utf-8')

for path in ('Shared/', 'Core/', 'Resources/', 'Platforms/', 'macOS/', 'Windows/'):
    assert path in readme
assert 'Shared/Tests' in runner
print('test_cross_platform_paths_static: OK')
