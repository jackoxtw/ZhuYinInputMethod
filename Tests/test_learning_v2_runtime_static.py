from pathlib import Path
root=Path(__file__).resolve().parents[1]
runtime=(root/'Platforms/macOS/App/ZYRuntime.mm').read_text(encoding='utf-8')
runtime_h=(root/'Platforms/macOS/App/ZYRuntime.h').read_text(encoding='utf-8')
controller=(root/'Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')
build=(root/'Platforms/macOS/scripts/build_and_install.command').read_text(encoding='utf-8')
installer=(root/'Platforms/macOS/Packaging/安裝逐音輸入法.command').read_text(encoding='utf-8')
learning_h=(root/'Shared/Core/ZYLearning.h').read_text(encoding='utf-8')
learning_c=(root/'Shared/Core/ZYLearning.c').read_text(encoding='utf-8')

assert 'ZYLEARN3' in learning_c and 'ZYLEARN2' in learning_c and 'ZYLEARN1' in learning_c
assert 'ZY_LEARN_WORD_CAP 4096' in learning_h
assert 'ZY_LEARN_QUERY_CAP 8192' in learning_h
assert 'ZY_LEARN_PHRASE_CAP 1024' in learning_h
assert 'uint64_t stable_key' in learning_h
assert 'uint32_t count' in learning_h
assert 'zy_learning_clear_persistent' in learning_h
assert 'F_SETLKW' in learning_c and '_locking' in learning_c
assert 'io_replace(tmp,path)' in learning_c.replace(' ','')

assert 'ZYRuntimeForceFlush' in runtime_h
assert 'dispatch_after' in runtime
assert 'zy_learning_record_word_stable' in runtime
assert 'dictionary_fingerprint' in runtime
assert 'stable_key' in runtime
assert 'BOOL canAdoptFingerprint=YES' in runtime
assert 'if(!map)canAdoptFingerprint=NO' in runtime.replace(' ','')
assert 'if(canAdoptFingerprint&&gLearning.p.dictionary_fingerprint!=current)' in runtime.replace(' ','')

close=controller[controller.index('- (void)inputControllerWillClose'):controller.index('- (void)deactivateServer:')]
deact=controller[controller.index('- (void)deactivateServer:'):controller.index('- (NSUInteger)recognizedEvents:')]
assert '_pieceCount' in close and 'learnAndCommit:' in close and '[self commitComposition:' not in close and 'ZYRuntimeForceFlush();' in close
assert '_pieceCount' in deact and 'learnAndCommit:' in deact and '[self commitComposition:' not in deact and 'ZYRuntimeForceFlush();' in deact

# The IME process gets a graceful termination chance before an emergency SIGKILL.
assert 'killall -9 ZhuYinInputMethod' not in build
assert 'killall -9 逐音輸入法' not in build
assert 'killall -9 ZhuYinInputMethod' not in installer

# Graceful IME shutdown must happen before replacing the installed bundle, so
# the old process can flush its current learning snapshot while its bundle is intact.
assert build.index('graceful_stop_ime') < build.index('sudo rm -rf "$DEST"')
assert installer.index("tell application id \"tw.zhuyin.inputmethod.v3\" to quit") < installer.index('sudo rm -rf "$DEST"')

print('test_learning_v2_runtime_static: OK')

assert '#ifdef _WIN32' in learning_c
assert 'io_open_read' in learning_c and 'io_open_write' in learning_c
print('test_learning_v3_portability_static: OK')
