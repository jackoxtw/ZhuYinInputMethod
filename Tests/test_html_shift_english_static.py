from pathlib import Path

html = Path('Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html').read_text(encoding='utf-8')

switch_start = html.index('function switchInputMode(){')
switch_end = html.index('function switchOutputScript(){', switch_start)
switch_block = html[switch_start:switch_end]
assert "if(state.inputMode==='zh' && state.pendingParts.length) finalizePending();" in switch_block
assert "state.composition=''" in switch_block
assert 'state.candidates=[]' in switch_block
assert 'commitCandidate()' not in switch_block

start = html.index("if(e.shiftKey && /^Digit[1-9]$/.test(e.code)")
end = html.index("const zhPunct=", start)
block = html[start:end]

# Shift+1–0/A–J candidate shortcuts must run before the Shift-English path.
assert block.index("/^Digit[1-9]$/.test(e.code)") < block.index("/^[a-z]$/i.test(e.key)"), \
    'Shift+1–9 candidate shortcuts must take priority over Shift English'
assert block.index("e.code==='Digit0'") < block.index("/^[a-z]$/i.test(e.key)"), \
    'Shift+0 candidate shortcut must take priority over Shift English'
assert block.index("/^Key[A-J]$/.test(e.code)") < block.index("/^[a-z]$/i.test(e.key)"), \
    'Shift+A–J candidate shortcuts must take priority over Shift English'

# Confirmed pending Chinese commits before unconfirmed composition is discarded and English is inserted.
assert 'if(state.pendingParts.length) finalizePending();' in block, \
    'Shift English must finalize confirmed pending Chinese'
assert "state.composition=''" in block
assert "state.candidates=[]" in block
assert 'handleEnglishChar(e.key.toLowerCase())' in block, \
    'Shift English must normalize the input letter before Caps Lock handling'
assert block.index('if(state.pendingParts.length) finalizePending();') < block.index("state.composition=''"), \
    'Confirmed pending Chinese must commit before composition is discarded'
assert block.index("state.composition=''") < block.index('handleEnglishChar(e.key.toLowerCase())'), \
    'Unconfirmed composition must be discarded before English is inserted'

# Chinese mode refreshes Caps Lock; single Shift remains controlled only on key release.
caps_refresh = "if(typeof e.getModifierState==='function') state.capsLock=!!e.getModifierState('CapsLock');"
assert caps_refresh in html and html.index(caps_refresh, start - 1200) < start, \
    'Chinese mode must refresh the current Caps Lock state before Shift English'
keyup_start = html.index("window.addEventListener('keyup',e=>")
keyup_block = html[keyup_start:html.index("window.addEventListener('resize'", keyup_start)]
assert "const toggle=shouldToggleShiftOnRelease(state.shiftDown,state.shiftUsed);" in keyup_block, \
    'Single Shift must retain the key-release toggle behavior'
print('test_html_shift_english_static: OK')
