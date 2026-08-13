from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / 'Resources/dictionary.bin'
FMT = '<8sIIIIII' + 'Q' * 15


def read_entries(path: Path):
    data = path.read_bytes()
    h = struct.unpack_from(FMT, data, 0)
    (magic, version, header_size, word_count, indexed_word_count, syllable_count, bucket_count,
     file_size, word_pool_off, word_pool_size, word_offsets_off, pron_offsets_off,
     syllable_ids_off, syllable_ids_count, weights_off, syllable_pool_off, syllable_pool_size,
     syllable_offsets_off, bucket_symbols_off, bucket_offsets_off, bucket_word_ids_off,
     bucket_word_ids_count) = h
    assert magic.startswith(b'ZYDICT1') and version == 1 and file_size == len(data)
    word_offsets = struct.unpack_from(f'<{word_count + 1}I', data, word_offsets_off)
    pron_offsets = struct.unpack_from(f'<{word_count + 1}I', data, pron_offsets_off)
    syllable_ids = struct.unpack_from(f'<{syllable_ids_count}H', data, syllable_ids_off)
    syllable_offsets = struct.unpack_from(f'<{syllable_count + 1}I', data, syllable_offsets_off)
    sylls = []
    for i in range(syllable_count):
        a, b = syllable_offsets[i], syllable_offsets[i + 1]
        sylls.append(data[syllable_pool_off + a: syllable_pool_off + b].decode('utf-8'))
    out = {}
    for wid in range(word_count):
        a, b = word_offsets[wid], word_offsets[wid + 1]
        word = data[word_pool_off + a: word_pool_off + b].decode('utf-8')
        pa, pb = pron_offsets[wid], pron_offsets[wid + 1]
        pron = tuple(sylls[syllable_ids[j]] for j in range(pa, pb))
        out.setdefault(word, set()).add(pron)
    return out

entries = read_entries(BIN)

# Taiwan pronunciations / polyphones that previously regressed to one PRC reading.
assert ('ㄑㄧˊ',) in entries.get('期', set())
assert ('ㄑㄧ',) not in entries.get('期', set())
assert {('ㄒㄧㄥˊ',), ('ㄏㄤˊ',)} <= entries.get('行', set())
assert {('ㄓㄨㄥˋ',), ('ㄔㄨㄥˊ',)} <= entries.get('重', set())
assert {('ㄓㄤˇ',), ('ㄔㄤˊ',)} <= entries.get('長', set())
assert {('ㄌㄜˋ',), ('ㄩㄝˋ',)} <= entries.get('樂', set())

# Same text must be allowed to have more than one pronunciation.
assert any(len(prons) > 1 for prons in entries.values())
