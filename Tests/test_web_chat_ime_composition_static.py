from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Platforms/macOS/App/ZYInputController.mm'


def source():
    return SOURCE.read_text(encoding='utf-8')


def method_body(text: str, signature: str):
    start = text.find(signature)
    assert start >= 0, f'{signature} not found'
    brace = text.find('{', start)
    assert brace >= 0
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[brace + 1:i]
    raise AssertionError(f'unclosed method {signature}')


def test_marked_text_is_published_directly_to_client_on_every_preedit_update():
    text = source()
    body = method_body(text, '- (void)updateMarked:(id)client')
    # Mature IMK implementations publish the active preedit directly to the
    # IMKTextInput client.  Do not rely on updateComposition's indirect path,
    # because web clients need their marked-text flag set before Return arrives.
    assert '[client setMarkedText:' in body
    assert 'inlineMarkedText' in body
    helper = method_body(text, '- (NSString *)inlineMarkedText')
    assert 'piecesText' not in helper
    assert 'preeditText' not in helper
    assert '[self updateComposition]' not in body


def test_controller_receives_keyup_as_well_as_keydown():
    text = source()
    body = method_body(text, '- (NSUInteger)recognizedEvents:(id)sender')
    assert 'NSEventMaskKeyDown' in body
    assert 'NSEventMaskKeyUp' in body
    assert 'NSEventMaskFlagsChanged' in body


def test_handled_keydown_has_matching_keyup_consumed():
    text = source()
    body = method_body(text, '- (BOOL)handleEvent:(NSEvent *)event client:(id)client')
    assert 'NSEventTypeKeyUp' in body
    assert '_handledKeyDown' in body
    assert 'return YES' in body


def test_enter_uses_same_immediate_ime_commit_path_for_main_and_keypad_return():
    text = source()
    enter = re.search(r'case 36:\s*\n\s*case 76:\s*\n\s*return \[self consumeReturnWhileComposing:client\];', text)
    assert enter, 'main Return and keypad Enter must share the IME-safe path'

    body = method_body(text, '- (BOOL)consumeReturnWhileComposing:(id)client')
    assert '[self publishMarkedText:client]' in body
    assert 'dispatch_async' not in body
    assert 'commitComposition:' not in body
    assert 'learnAndCommit:' in body
    assert 'return YES' in body


def test_enter_selects_only_one_candidate_while_zhuyin_remains():
    text = source()
    body = method_body(text, '- (BOOL)consumeReturnWhileComposing:(id)client')
    compact = re.sub(r'\s+', '', body)

    # Return must not consume all remaining syllables and immediately commit
    # them.  While raw Zhuyin remains, it only accepts the highlighted item.
    assert 'for(intguard=0;_composition.length&&guard<16;guard++)' not in compact
    assert 'if(_composition.length){if(_candidateCount)return[selfchooseSelected:client];' in compact
    assert 'if(_pieceCount){[selflearnAndCommit:client];returnYES;}' in compact


def test_commit_clears_marked_text_through_same_direct_client_path():
    text = source()
    body = method_body(text, '- (void)learnAndCommit:(id)client')
    assert '[self updateMarked:client]' in body
    assert '[self updateComposition]' not in body

    body = method_body(text, '- (void)commitComposition:(id)sender')
    assert '[self updateMarked:client]' in body
    assert '[self updateComposition]' not in body


if __name__ == '__main__':
    for name in sorted(globals()):
        if name.startswith('test_'):
            globals()[name]()
    print('test_web_chat_ime_composition_static: OK')
