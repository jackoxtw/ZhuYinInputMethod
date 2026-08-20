from pathlib import Path
s = (Path(__file__).resolve().parents[1] / 'Platforms/macOS/scripts/build_and_install.command').read_text('utf-8')
assert 'repair_dictionary_taiwan.py' in s
assert 'libchewing-data' in s
assert 'word.csv' in s
assert 'Shared/Resources/dictionary.bin' in s  # offline fallback is already core-repaired
# Repair must happen before the dictionary is copied into the app bundle.
assert s.index('repair_dictionary_taiwan.py') < s.index('cp "$DICT_FOR_BUILD" "$RES/dictionary.bin"')

assert 'inject_dictionary_words.py' in s
assert 'Shared/Resources/brand_words.csv' in s
assert s.index('repair_dictionary_taiwan.py') < s.index('inject_dictionary_words.py') < s.index('cp "$DICT_FOR_BUILD" "$RES/dictionary.bin"')
