from pathlib import Path

src = (Path(__file__).resolve().parents[1] / 'Platforms/macOS/App/ZYRuntime.mm').read_text(encoding='utf-8')
assert '@interface ZYRuntimeLockToken' in src
assert '#define ZY_RUNTIME_SYNCHRONIZED @synchronized([ZYRuntimeLockToken class])' in src
for fn in (
    'ZYRuntimeInitialize', 'ZYRuntimeLookup', 'ZYRuntimeBeginLearningEvent',
    'ZYRuntimeLearnWord', 'ZYRuntimeRemoveCandidateLearning',
    'ZYRuntimeCandidateHasLearning', 'ZYRuntimeLearnPhrase',
    'ZYRuntimeCandidatePron', 'ZYRuntimeCandidateWord', 'ZYRuntimeOutputString',
    'ZYRuntimeClearLearning', 'ZYRuntimeMaybeFlush', 'ZYRuntimeForceFlush',
    'ZYRuntimeShutdown',
):
    import re
    match = re.search(r'^(?:BOOL|void|size_t|int|NSString\s*\*)\s*' + re.escape(fn) + r'\(', src, re.M)
    start = match.start() if match else -1
    assert start >= 0, fn
    body = src[start:start + 1800]
    assert 'ZY_RUNTIME_SYNCHRONIZED' in body, fn
assert 'dispatch_after' in src
block = src[src.find('dispatch_after'):src.find('void ZYRuntimeForceFlush')]
assert 'ZY_RUNTIME_SYNCHRONIZED' in block
print('runtime learning lock static: OK')
