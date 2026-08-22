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


def test_controller_sends_pending_text_and_unfinished_zhuyin_separately():
    source = text(CONTROLLER)
    body = method_body(source, '- (void)refreshPanel:(id)client')
    assert '[panel setPreeditText:[self piecesText]]' in body
    assert '[panel setZhuyinText:_composition]' in body
    assert 'floatingPreeditText' not in body


def test_candidate_panel_exposes_dedicated_zhuyin_text_api():
    header = text(PANEL_H)
    panel = text(PANEL_MM)
    assert '- (void)setZhuyinText:(NSString *)text;' in header
    assert '@property(nonatomic,copy) NSString *zhuyinText;' in panel
    body = method_body(panel, '- (void)setZhuyinText:(NSString *)text')
    assert '_cv.zhuyinText' in body
    assert 'resizeForRows:' in body


def test_unfinished_zhuyin_is_drawn_in_right_hand_column_and_left_aligned():
    panel = text(PANEL_MM)
    assert 'ZYPreeditZhuyinColumnX' in panel
    assert 'ZYPreeditZhuyinColumnWidth' in panel
    assert 'zhuyinRect' in panel
    assert 'self.zhuyinText' in panel
    # Explicit alignment prevents natural/right alignment from changing with locale.
    attrs = panel[panel.find('static NSDictionary *ZYPreeditTextAttributes'):]
    attrs = attrs[:attrs.find('@implementation ZYCandidateView')]
    assert 'paragraph.alignment=NSTextAlignmentLeft' in attrs


def test_preedit_header_remains_visible_for_pending_or_unfinished_text():
    panel = text(PANEL_MM)
    implementation = panel[panel.find('@implementation ZYCandidateView'):]
    body = method_body(implementation, '- (CGFloat)preeditHeaderHeight')
    assert 'self.preeditText.length' in body
    assert 'self.zhuyinText.length' in body
