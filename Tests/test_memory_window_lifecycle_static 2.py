from pathlib import Path
root = Path(__file__).resolve().parents[1]
h = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.h').read_text(encoding='utf-8')
p = (root/'Platforms'/'macOS'/'App'/'ZYCandidatePanel.mm').read_text(encoding='utf-8')
c = (root/'Platforms'/'macOS'/'App'/'ZYInputController.mm').read_text(encoding='utf-8')

# Panel must not retain the controller. The controller already owns the panel.
assert '@property(nonatomic,weak) id<ZYCandidatePanelDelegate> candidateDelegate;' in h

# Candidate window must be lazy: controller init should not allocate NSPanel.
init_start = c.find('- (instancetype)initWithServer:')
init_end = c.find('- (ZYCandidatePanel *)ensureCandidatePanel', init_start)
init_block = c[init_start:init_end]
assert '[[ZYCandidatePanel alloc]init]' not in init_block
assert '- (ZYCandidatePanel *)ensureCandidatePanel' in c
assert '_panel=[[ZYCandidatePanel alloc]init]' in c

# Closing/deactivating an input session must release the candidate panel.
assert '- (void)releaseCandidatePanel' in c
close_start = c.find('- (void)inputControllerWillClose')
close_end = c.find('- (void)deactivateServer:', close_start)
assert '[self releaseCandidatePanel]' in c[close_start:close_end]
deact_start = c.find('- (void)deactivateServer:')
deact_end = c.find('- (NSUInteger)recognizedEvents:', deact_start)
assert '[self releaseCandidatePanel]' in c[deact_start:deact_end]

# Auxiliary windows must release their views/backing store when closed.
help_start = p.find('- (void)closeQuickHelp')
help_end = p.find('- (void)orderOut:', help_start)
help = p[help_start:help_end]
assert '_helpView.owner=nil' in help
assert '_helpPanel.contentView=nil' in help
assert '[_helpPanel close]' in help
assert '_helpView=nil' in help
assert '_helpPanel=nil' in help

clear_start = p.find('- (void)closeClearLearningConfirmation')
clear_end = p.find('- (void)showClearLearningResult:', clear_start)
clear = p[clear_start:clear_end]
assert '_clearLearningView.owner=nil' in clear
assert '_clearLearningPanel.contentView=nil' in clear
assert '[_clearLearningPanel close]' in clear
assert '_clearLearningView=nil' in clear
assert '_clearLearningPanel=nil' in clear
print('memory window lifecycle static: OK')
