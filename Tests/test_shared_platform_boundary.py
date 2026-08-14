from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for source in (ROOT / 'Shared/Core').glob('*.[ch]'):
    text = source.read_text(encoding='utf-8')
    assert '#import' not in text
    assert 'Cocoa/' not in text
    assert 'windows.h' not in text.lower()
assert (ROOT / 'Shared/Resources/dictionary.bin').is_file()
assert (ROOT / 'Shared/Resources/t2s.bin').is_file()

print('shared platform boundary: OK')
