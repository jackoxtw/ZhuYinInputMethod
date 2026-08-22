from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms' / 'macOS' / 'App' / 'ZYInputController.mm').read_text('utf-8')

# Candidate shortcuts must remain ahead of Latin Shift handling.
shortcut = 'if(_candidateCount&&shift){NSInteger slot=shiftSlot(event.keyCode);'
latin_marker = 'if(shift&&isASCIIEnglishLetter(event.characters))'
assert shortcut in controller
assert latin_marker in controller
assert controller.index(shortcut) < controller.index(latin_marker), 'candidate Shift shortcuts must keep priority'

# With no candidate active, Shift+letter case is controlled only by Caps Lock.
latin_start = controller.index(latin_marker)
latin_end = controller.index('NSUInteger pageSize=', latin_start)
latin_block = controller[latin_start:latin_end]
assert 'NSEventModifierFlagCapsLock' in latin_block, 'Shift Latin path must read Caps Lock explicitly'
assert '_candidateCount' in latin_block, 'Caps-only casing must be scoped to no-candidate input'
assert 'lowercaseString' in latin_block, 'Caps Lock off must normalize Shift+letter to lowercase'
assert 'uppercaseString' in latin_block, 'Caps Lock on must normalize Shift+letter to uppercase'
assert '[self chooseSelected:client]' not in latin_block, \
    'Shift English must not commit an unconfirmed selected candidate'
assert '[_composition setString:@""]' in latin_block, \
    'Shift English must discard unconfirmed Zhuyin composition'
assert '[self showInternalState:client]' in latin_block, \
    'Discarding composition must also clear marked text and candidate UI'
assert 'if(_pieceCount)[self learnAndCommit:client];' in latin_block, \
    'Already confirmed pieces must still commit before Latin input'

# Shift-alone language toggles must commit confirmed pieces but discard any
# unconfirmed composition instead of selecting/committing a candidate.
toggle_start = controller.index('- (void)toggleLanguage:')
toggle_end = controller.index('- (void)toggleScript:', toggle_start)
toggle = controller[toggle_start:toggle_end]
assert '[self chooseSelected:client]' not in toggle
assert 'if(_pieceCount)[self learnAndCommit:client];' in toggle
assert '[_composition setString:@""]' in toggle
assert '[self showInternalState:client]' in toggle

# Idle Space must bypass pending punctuation/learning and insert a real space directly.
space_case = controller.split('case 49:', 1)[1].split('case 36:', 1)[0]
assert '[client insertText:@" " replacementRange:NSMakeRange(NSNotFound,NSNotFound)]' in space_case, 'idle Space must insert directly into client'
assert '_pieceCount' in space_case and '_candidateCount' in space_case, 'direct Space must be restricted to a truly idle input state'
assert '[self appendPunctuation:@" " client:client]' in space_case, 'pending-piece Space behavior must remain available'

print('test_idle_space_caps_shift_static: OK')
