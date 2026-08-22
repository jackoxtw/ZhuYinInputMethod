from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / 'Platforms/macOS/App/ZYInputController.mm'


def text(path):
    return path.read_text(encoding='utf-8')


def method_body(source: str, signature: str):
    start = source.find(signature)
    assert start >= 0, f'{signature} not found'
    brace = source.find('{', start)
    assert brace >= 0
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[brace + 1:i]
    raise AssertionError(f'unclosed method {signature}')


def test_return_uses_repeat_guard_not_persistent_keyup_latch():
    body = method_body(text(CONTROLLER), '- (BOOL)handleEvent:(NSEvent *)event client:(id)client')
    assert 'if((key==36||key==76)&&event.isARepeat)return YES;' in body
    assert 'if((key==36||key==76)&&_handledKeyDown[key])return YES;' not in body
    assert 'event.isARepeat||_handledKeyDown[key]' not in body


def test_handled_return_is_not_recorded_in_keydown_latch():
    body = method_body(text(CONTROLLER), '- (BOOL)handleEvent:(NSEvent *)event client:(id)client')
    # Other handled keys may still use keyUp pairing, but Return/Enter must not:
    # IMK may omit their keyUp, which would permanently lock later Return presses.
    assert 'if(key<256&&key!=36&&key!=76)_handledKeyDown[key]=YES;' in body
    assert 'BOOL handled=[self handleInputEvent:event client:client];' in body
