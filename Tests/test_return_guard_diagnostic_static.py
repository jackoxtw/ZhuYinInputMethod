from pathlib import Path
p=Path(__file__).resolve().parents[1]/'Docs/Diagnostics/return_guard_test.html'
s=p.read_text(encoding='utf-8')
for token in ['compositionstart','compositionend','keydown','keyup','isComposing','keyCode','Enter']:
    assert token in s, token
assert '組字中的 Enter keydown' in s
assert '組字中的 Enter keyup' in s
print('test_return_guard_diagnostic_static: OK')
