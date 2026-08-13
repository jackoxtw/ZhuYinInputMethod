from pathlib import Path

root = Path(__file__).resolve().parents[1]
header = (root / 'App/ZYCandidatePanel.h').read_text('utf-8')
panel = (root / 'App/ZYCandidatePanel.mm').read_text('utf-8')
controller = (root / 'App/ZYInputController.mm').read_text('utf-8')

# Candidate UI must expose the same output-script toggle concept as the web version.
assert '- (void)candidatePanelToggleScript;' in header, 'candidate panel delegate must expose script toggle callback'
assert '_cv.simplified=simplified;' in panel, 'panel must retain simplified state passed by controller'
assert 'NSString *scriptLabel=self.simplified?@"簡":@"繁";' in panel, 'panel must render current script label'
assert 'NSMakeRect(732,28,48,32)' in panel, 'candidate panel must reserve a 48x32 script button beside candidates'
assert '[self.panel candidateViewToggleScript]' in panel, 'view click must route to panel'
assert '[self.candidateDelegate candidatePanelToggleScript]' in panel, 'panel must forward script click to controller'
assert 'NSMakeRect(0,0,786,110)' in panel, 'panel width must include candidate grid plus script/help/clear controls'

# The controller owns the single source of truth and persists it like the web version.
assert 'static NSString *const ZYOutputSimplifiedKey=@"ZYOutputSimplified";' in controller
assert ('_simplified=[[NSUserDefaults standardUserDefaults] boolForKey:ZYOutputSimplifiedKey];' in controller or '_simplified=[defaults boolForKey:ZYOutputSimplifiedKey];' in controller), 'saved script mode must load on controller init'
assert 'setBool:_simplified forKey:ZYOutputSimplifiedKey' in controller, 'toggle must persist the new script mode'
assert '- (void)candidatePanelToggleScript { [self toggleScript:[self client]]; }' in controller, 'candidate panel button must share the existing toggleScript path'

# Simplified conversion remains final-output-only: candidates and learning stay traditional.
assert 'ZYRuntimeOutputString(text,_simplified)' in controller
assert '[panel updateCandidates:' in controller
print('test_script_toggle_static: OK')
