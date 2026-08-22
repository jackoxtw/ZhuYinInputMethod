from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / 'Platforms/macOS/App/ZYInputController.mm'
PANEL_H = ROOT / 'Platforms/macOS/App/ZYCandidatePanel.h'
PANEL_MM = ROOT / 'Platforms/macOS/App/ZYCandidatePanel.mm'


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


def test_pending_and_unfinished_zhuyin_stay_out_of_client_document():
    src = text(CONTROLLER)
    body = method_body(src, '- (NSString *)inlineMarkedText')
    # Port the working HTML model: selected pieces and raw Zhuyin stay in the
    # candidate UI until final confirmation. The client gets only an invisible
    # IME placeholder while an internal composition exists.
    assert 'piecesText' not in body
    assert '_pieceCount' in body
    assert '_composition.length' in body
    assert '\\u2060' in body


def test_candidate_header_shows_pending_text_and_unfinished_zhuyin_separately():
    src = text(CONTROLLER)
    panel_body = method_body(src, '- (void)refreshPanel:(id)client')
    assert '[panel setPreeditText:[self piecesText]]' in panel_body
    assert '[panel setZhuyinText:_composition]' in panel_body
    assert '[panel setPreeditLabel:' in panel_body

    header = text(PANEL_H)
    assert '- (void)setPreeditLabel:(NSString *)label;' in header
    assert '- (void)setZhuyinText:(NSString *)text;' in header
    panel_src = text(PANEL_MM)
    assert '@property(nonatomic,copy) NSString *preeditLabel;' in panel_src
    assert '@property(nonatomic,copy) NSString *zhuyinText;' in panel_src
    assert 'ZYPreeditZhuyinColumnX' in panel_src


def test_one_physical_return_cannot_advance_more_than_once():
    src = text(CONTROLLER)
    body = method_body(src, '- (BOOL)handleEvent:(NSEvent *)event client:(id)client')
    assert 'event.type==NSEventTypeKeyDown' in body
    assert 'event.isARepeat' in body
    assert 'key==36||key==76' in body
    # Unlike browser JS, InputMethodKit may omit Return keyUp.  The native port
    # therefore uses NSEvent's repeat flag instead of a persistent Return latch.
    assert 'event.isARepeat||_handledKeyDown[key]' not in body
    assert 'if(key<256&&key!=36&&key!=76)_handledKeyDown[key]=YES;' in body
    # The repeat guard must happen before normal input routing.
    assert body.find('event.isARepeat') < body.find('[self handleInputEvent:event client:client]')


def test_return_candidate_then_finalize_then_pass_through_are_three_distinct_presses():
    src = text(CONTROLLER)
    body = method_body(src, '- (BOOL)consumeReturnWhileComposing:(id)client')
    candidate = body.find('if(_candidateCount)')
    composition = body.find('if(_composition.length)', candidate)
    staged = body.find('if(_pieceCount)', composition)
    assert 0 <= candidate < composition < staged
    branch = body[candidate:composition]
    assert '[self chooseSelected:client]' in branch
    assert 'return YES' in branch
    assert 'learnAndCommit:' not in branch
    assert '[self learnAndCommit:client]' in body[staged:]


def test_punctuation_does_not_auto_select_all_remaining_candidates():
    src = text(CONTROLLER)
    body = method_body(src, '- (void)appendPunctuation:(NSString *)punct client:(id)client')
    assert 'for(int guard=' not in body
    assert 'if(_composition.length)' in body
    assert '[self chooseSelected:client]' in body
    assert 'if(_composition.length)' in body[body.find('[self chooseSelected:client]'):]

def test_escape_clearing_staged_text_also_closes_or_refreshes_candidate_panel():
    src = text(CONTROLLER)
    body = method_body(src, '- (BOOL)handleInputEvent:(NSEvent *)event client:(id)client')
    marker = 'if(_pieceCount){_pieceCount=0;[self updateMarked:client];'
    start = body.find(marker)
    assert start >= 0
    branch = body[start:body.find('return NO;', start)]
    assert '[self refreshPanel:client]' in branch or '[self hideCandidatePanel]' in branch
