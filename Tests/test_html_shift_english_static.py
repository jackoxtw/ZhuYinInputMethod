from pathlib import Path

html = Path('Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html').read_text(encoding='utf-8')
start = html.index("if(e.shiftKey && /^Key[A-J]$/.test(e.code)")
end = html.index("const zhPunct=", start)
block = html[start:end]

assert "state.composition=''" in block
assert "state.candidates=[]" in block
assert 'handleEnglishChar(e.key)' in block
print('test_html_shift_english_static: OK')
