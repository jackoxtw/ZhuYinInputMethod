from pathlib import Path

# The per-key live diagnostic harness is intentionally absent from the release
# tree.  It relied on CFPreferences synchronization in the hot path and is now
# superseded by Instruments / vmmap profiling.
assert not Path('Tools/逐音輸入法_候選視窗記憶體測試.command').exists(), \
    'release tree must not ship the per-key memory diagnostic command'
print('release memory diagnostic command removal static regression test: OK')
