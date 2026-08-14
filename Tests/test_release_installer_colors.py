from pathlib import Path

installer = (Path(__file__).resolve().parents[1] / 'Release' / '逐音輸入法-v0.1.47' / '安裝逐音輸入法.command').read_text(encoding='utf-8')

for token in ['C_BLUE=', 'C_CYAN=', 'C_GREEN=', 'C_YELLOW=', 'C_RED=', 'C_RESET=',
              'step(){', 'info(){', 'success(){', 'warn(){', 'fail(){']:
    assert token in installer, f'missing release installer color helper: {token}'

for message in ['檢查 Release 內容', '驗證 App 完整性', '安裝到系統輸入法目錄', '安裝完成']:
    assert message in installer, f'missing colored release installer phase: {message}'

print('release installer colors: OK')
