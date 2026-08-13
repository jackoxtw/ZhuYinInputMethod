from pathlib import Path

src = Path('App/ZYRuntime.mm').read_text(encoding='utf-8')

bad = 'initWithFileSystemRepresentation:gLearningBase length:strlen(gLearningBase)'
assert bad not in src, 'NSString does not implement initWithFileSystemRepresentation:length:'
assert '[fm stringWithFileSystemRepresentation:gLearningBase length:strlen(gLearningBase)]' in src, \
    'learning path must be reconstructed through NSFileManager file-system representation API'
print('learning path bridge static regression: OK')
