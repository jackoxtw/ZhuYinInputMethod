from pathlib import Path
h = Path('Platforms/macOS/App/ZYCandidatePanel.h').read_text(encoding='utf-8')
p = Path('Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')
c = Path('Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')
assert '@property(nonatomic,weak) id<ZYCandidatePanelDelegate> candidateDelegate;' in h, 'controller owns panel, so panel delegate must stay weak to avoid a retain cycle'
assert '@property(nonatomic,weak) ZYCandidatePanel *panel;' in p, 'view must point back only to its owning panel'
assert '_cv.panel=self;' in p, 'panel must install itself as view action owner'
assert '[self.panel candidateViewDidChooseIndex:idx]' in p, 'view candidate click must route through panel'
assert '[self.panel candidateViewToggleScript]' in p
assert '[self.panel candidateViewToggleHelp]' in p
assert '[self.panel candidateViewRequestClearLearning]' in p
assert '[self.candidateDelegate candidatePanelDidChooseIndex:index]' in p, 'panel must forward candidate action to controller'
assert '[self.candidateDelegate candidatePanelRequestClearLearning]' in p
assert '[self.candidateDelegate candidatePanelConfirmClearLearning]' in p
close = c[c.find('- (void)inputControllerWillClose'):c.find('- (void)deactivateServer:')]
assert '[self releaseCandidatePanel]' in close, 'controller must release the panel when session closes'
print('candidate delegate routing static: OK')
