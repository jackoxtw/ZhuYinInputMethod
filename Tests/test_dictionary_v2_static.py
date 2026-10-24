from pathlib import Path
import struct
root=Path(__file__).resolve().parents[1]
c=(root/'Shared/Core/ZYDictionary.c').read_text(encoding='utf-8')
b=(root/'Shared/Tools/build_native_dictionary.py').read_text(encoding='utf-8')
data=(root/'Shared/Resources/dictionary.bin').read_bytes()
magic,version=struct.unpack_from('<8sI',data,0)
assert magic.startswith(b'ZYDICT2') and version==2
assert 'ZYDICT1' in c and 'ZYDICT2' in c
assert 'validate_dictionary' in c
for token in ['offsets_ok','syllable_ids[i]>=h->syllable_count','bucket_word_ids[i]>=h->word_count']:
    assert token in c, token
assert "MAGIC=b'ZYDICT2\\0'" in b or "MAGIC=b'ZYDICT2\0'" in b
assert '#ifdef _WIN32' in c and 'fopen(path,"rb")' in c
print('test_dictionary_v2_static: OK')
