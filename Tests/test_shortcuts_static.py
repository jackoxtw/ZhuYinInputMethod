from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'App/ZYInputController.mm').read_text('utf-8')
header = (root / 'App/ZYCandidatePanel.h').read_text('utf-8')
panel = (root / 'App/ZYCandidatePanel.mm').read_text('utf-8')

# F9 must reuse the existing persisted simplified/traditional toggle path.
assert 'case kVK_F9:' in controller, 'F9 must be handled by Carbon key code'
assert '[self toggleScript:client];return YES;' in controller, 'F9 must call the same persisted toggleScript path'
assert controller.index('case kVK_F9:') < controller.index('if(!_chinese)return NO;'), 'F9 must also work while English mode is active'

# Backtick and apostrophe open special candidate lists without changing the language model.
assert 'ZYSpecialCandidateEmoji' in controller
assert 'ZYSpecialCandidatePunctuation' in controller
assert 'case kVK_ANSI_Grave:' in controller, 'unshifted ` must open emoji candidates'
assert 'case kVK_ANSI_Quote:' in controller, "unshifted ' must open punctuation candidates"
assert '[self openSpecialCandidates:ZYSpecialCandidateEmoji client:client];' in controller
assert '[self openSpecialCandidates:ZYSpecialCandidatePunctuation client:client];' in controller

# Special candidates are staged as non-learning output and reuse paging / selection.
assert '- (BOOL)chooseSpecialAbsolute:(NSUInteger)idx client:(id)client' in controller
assert 'p->kind=ZYPiecePunctuation;' in controller, 'special entries must be excluded from word learning'
assert '- (void)updateWords:(NSArray<NSString*> *)words' in header
assert 'modeLabel' in panel, 'candidate window should identify Emoji / punctuation mode'
assert 'Emoji' in controller and '標點' in controller

# Escape closes a special list without destroying the existing composition.
assert 'if(_specialMode!=ZYSpecialCandidateNone){[self closeSpecialCandidates:client];return YES;}' in controller

print('test_shortcuts_static: OK')

# Special lists use 50 items per page / up to five rows; normal Zhuyin stays 20 / two rows.
assert 'ZYSpecialPageSize' in controller, 'special candidate page-size helper/constant must exist'
assert 'returnmode==ZYSpecialCandidateNone?20:50;' in controller.replace(' ', ''), 'page size must be 20 normal / 50 special'
assert '_pageStart=(_selected/pageSize)*pageSize;' in controller, 'refreshPanel must page by active mode size'
assert '_selected>=pageSize?_selected-pageSize:0' in controller, 'Page Up must use active page size'
assert '_selected+pageSize' in controller, 'Page Down must use active page size'
assert '@property(nonatomic) NSUInteger count,selected,rows,columns;' in panel, 'candidate view must track dynamic rows and columns'
assert 'MIN(count,(NSUInteger)50)' in panel, 'special word candidates must allow up to 50 items'
assert 'rows=MIN((NSUInteger)5,MAX((NSUInteger)1,(count+9)/10));' in panel.replace(' ', ''), 'special rows must be dynamically capped at five'
assert 'maxChars<=2?10:(maxChars<=5?5:4)' in panel.replace(' ', ''), 'normal candidates must use adaptive 10/5/4-column layout'
assert '_cv.rowHeight=columns==10?38:(columns==5?48:58);' in panel.replace(' ', ''), 'adaptive normal layout must use readable row heights'
assert 'row<self.rows' in panel, 'mouse hit testing must support all visible special rows'
assert '12.0+_cv.rowHeight*rows' in panel.replace(' ', ''), 'panel content height must grow with active row height'
assert '_cv.columns=10;_cv.rowHeight=38;' in panel.replace(' ', ''), 'Emoji/punctuation mode must keep the existing ten-column compact grid'

# Script button keeps its main 繁/簡 label and advertises the F9 shortcut unobtrusively.
assert '@"F9"' in panel, 'script toggle button must show an F9 hint'
assert 'systemFontOfSize:7.5' in panel or 'systemFontOfSize:8' in panel, 'F9 hint must stay visually secondary'
assert 'scriptLabel=self.simplified?@"簡":@"繁";' in panel, 'F9 hint must not replace the main script label'
