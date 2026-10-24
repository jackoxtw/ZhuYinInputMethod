from pathlib import Path

src = Path('Platforms/macOS/App/ZYRuntime.mm').read_text(encoding='utf-8')

bad = 'initWithFileSystemRepresentation:gLearningBase length:strlen(gLearningBase)'
assert bad not in src, 'NSString does not implement initWithFileSystemRepresentation:length:'
assert 'strlcpy(gLearningBase,base.fileSystemRepresentation,sizeof(gLearningBase))' in src, \
    'learning path must originate from NSString fileSystemRepresentation so the Traditional-Chinese path remains filesystem-safe'
assert 'zy_learning_clear_persistent(&gLearning,gLearningBase' in src, \
    'clear-learning must use the already validated filesystem path instead of rebuilding it through an invalid NSString initializer'
print('learning path bridge static regression: OK')
