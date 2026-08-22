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


def test_all_pending_text_is_kept_out_of_inline_marked_text():
    source = text(CONTROLLER)
    body = method_body(source, '- (void)updateMarked:(id)client')
    assert 'inlineMarkedText' in body
    helper = method_body(source, '- (NSString *)inlineMarkedText')
    assert 'piecesText' not in helper
    assert 'preeditText' not in helper
    assert '@"\\u2060"' in helper


def test_candidate_panel_has_dedicated_popup_preedit_api():
    header = text(PANEL_H)
    panel = text(PANEL_MM)
    assert '- (void)setPreeditText:(NSString *)text;' in header
    assert '@property(nonatomic,copy) NSString *preeditText;' in panel
    body = method_body(panel, '- (void)setPreeditText:(NSString *)text')
    assert '_cv.preeditText' in body
    assert 'resizeForRows:' in body


def test_popup_preedit_is_drawn_above_candidate_rows():
    panel = text(PANEL_MM)
    assert 'ZYPreeditHeaderHeight' in panel
    assert 'self.preeditText' in panel
    assert 'preeditY' in panel
    # Candidate row origin must be shifted below the popup preedit header.
    assert 'y0=self.preeditHeaderHeight+6' in panel


def test_panel_shows_all_pending_text_even_without_candidates():
    source = text(CONTROLLER)
    body = method_body(source, '- (void)refreshPanel:(id)client')
    assert 'NSString *preedit=[self preeditText];' in body
    assert 'setPreeditText:' in body
    assert '!_candidateCount&&!preedit.length' in body.replace(' ', '')


def test_caret_lookup_does_not_index_by_hidden_zhuyin_length():
    source = text(CONTROLLER)
    body = method_body(source, '- (NSRect)clientRect:(id)client')
    assert '[self preeditText].length' not in body
    assert 'selectedRange' in body


def test_imk_composed_string_never_returns_raw_zhuyin_preedit():
    source = text(CONTROLLER)
    body = method_body(source, '- (id)composedString:(id)sender')
    assert 'inlineMarkedText' in body
    assert 'preeditText' not in body


def test_enter_never_commits_unresolved_zhuyin_as_literal_text():
    source = text(CONTROLLER)
    body = method_body(source, '- (BOOL)consumeReturnWhileComposing:(id)client')
    assert 'commitComposition:' not in body
    assert 'learnAndCommit:' in body
    assert 'NSBeep' in body
    assert 'return YES' in body


def test_commit_callback_never_auto_selects_unfinished_zhuyin():
    source = text(CONTROLLER)
    body = method_body(source, '- (void)commitComposition:(id)sender')
    unresolved = body[body.find('if(_composition.length)'):]
    assert '[client insertText:' not in unresolved
    assert '[self chooseSelected:client]' not in unresolved
    assert 'for(int guard=0;_composition.length&&guard<16;guard++)' not in unresolved
    assert '[selfrefreshCandidates:client];return;' in unresolved.replace(' ', '')
