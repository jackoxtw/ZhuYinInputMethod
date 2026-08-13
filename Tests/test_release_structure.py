from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / 'README.md').read_text(encoding='utf-8')

required = [
    '# 逐音輸入法',
    '## 主要功能',
    '## 系統需求',
    '## 安裝',
    '## 快捷鍵與候選操作',
    '## 繁／簡輸出',
    '## Emoji 與中文標點',
    '## 台灣注音與多音字詞庫',
    '## 資料寫入與隱私',
    '## 專案目錄結構',
    '## 測試與開發',
    '## 解除安裝',
    '## 常見問題',
    '## 第三方資料與授權',
]
for heading in required:
    assert heading in readme, f'missing README section: {heading}'

assert 'F9' in readme
assert '`（反引號）' in readme or '反引號' in readme
assert "'（單引號）" in readme or '單引號' in readme
assert 'OpenCC 1.3.1' in readme
assert 'libchewing-data' in readme
assert '/Library/Input Methods/逐音輸入法.app' in readme

root_html = list(ROOT.glob('*.html'))
assert not root_html, f'legacy HTML must not stay in project root: {root_html}'
legacy = ROOT / 'Docs' / 'Reference' / '台灣注音輸入法_Canvas_單檔版(20260812-065531).html'
assert legacy.is_file(), 'legacy Canvas HTML missing from Docs/Reference'

assert (ROOT / 'Docs' / 'Development' / 'plans').is_dir()
assert (ROOT / 'Docs' / 'Development' / 'specs').is_dir()
assert not (ROOT / 'docs').exists(), 'old lowercase docs directory should be removed'

for path in ['App', 'Core', 'Resources', 'Tools', 'Tests', 'Licenses']:
    assert (ROOT / path).is_dir(), f'build-critical directory missing: {path}'

runner = (ROOT / 'run_core_tests.sh').read_text(encoding='utf-8')
assert 'Tests/test_release_structure.py' in runner, 'main test runner must include release structure regression'

print('test_release_structure: OK')
