from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = (root / 'Platforms' / 'macOS' / 'App' / 'ZYRuntime.mm').read_text()
h = (root / 'Shared' / 'Core' / 'ZYComposer.h').read_text()
c = (root / 'Shared' / 'Core' / 'ZYComposer.c').read_text()

assert 'substringWithRange:' not in s, 'Runtime lookup must not allocate NSString substrings per segment'
assert 'ZYRuntimeQueryHashCodepointRange' in s
assert 'ZYRuntimeQueryCodepointOffsets' in s
assert 'zy_composer_lookup_with_workspace(&gEngine,query' in s
assert 'ZYComposerWorkspace gComposerWorkspace' in s
assert 'zy_composer_workspace_init(&gComposerWorkspace)' in s

assert 'typedef struct' in h and 'ZYComposerWorkspace' in h
assert 'zy_composer_lookup_with_workspace' in h
assert 'zy_composer_workspace_init' in h
assert 'zy_composer_workspace_dispose' in h

# The optimized path owns reusable storage; the hot lookup body must not directly
# allocate and free beam arrays each key press.
lookup_body = c[c.index('size_t zy_composer_lookup_with_workspace'):]
assert 'calloc(slots*ZY_COMPOSER_BEAM_WIDTH' not in lookup_body
assert 'free(counts);free(beams)' not in lookup_body
print('test_runtime_allocation_static: OK')
