from pathlib import Path

root = Path(__file__).resolve().parents[1]
build = (root / 'Platforms/macOS/scripts/build_and_install.command').read_text('utf-8')

# ANSI colors must be optional and disabled for non-interactive output.
assert '[[ -t 1' in build, 'installer must only emit colors to an interactive terminal'
for token in ['C_BLUE=', 'C_CYAN=', 'C_GREEN=', 'C_YELLOW=', 'C_RED=', 'C_MAGENTA=', 'C_DIM=', 'C_RESET=']:
    assert token in build, f'missing installer color token {token}'

# Reusable semantic helpers keep commands visually consistent.
for fn in ['step()', 'info()', 'success()', 'warn()', 'fail()', 'meta()']:
    assert fn in build, f'missing color helper {fn}'

# Important installer phases should be visibly separated.
for label in ['檢查編譯環境', '更新台灣注音詞庫', '建立簡體轉換資料', '建立 App 圖示', '編譯逐音輸入法', '簽署與驗證 App', '安裝與重新註冊輸入法']:
    assert label in build, f'missing colored installer phase: {label}'

# Success/warning output should go through semantic helpers rather than raw symbols.
assert 'success "已套用 libchewing-data 完整台灣注音／多音字讀音"' in build
assert 'success "已套用 OpenCC 1.3.1 完整台灣正體→簡體 tw2s 規則"' in build
assert 'warn "無法取得或驗證完整 OpenCC 1.3.1 tw2s' in build

print('test_colored_installer: OK')
