# Task 2 Report

## 變更

- 更新 `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`
  - 特殊候選面板改用 `activeCandidates()` / `candidatePageSize()`，特殊模式固定 10 欄、50 格呈現。
  - `chooseSelectedCandidate()` 接受索引，滑鼠點擊特殊候選改走同一條選取路徑；一般候選仍保留 Option 刪除學習。
  - `resize()` 提高 canvas 高度到桌面 `1145` / 行動 `1060`，保留特殊 5 列候選和下方鍵盤／控制列。
  - 頂部 note 改為「取消未確認注音」的正確描述，並連到頁底完整說明。
  - 新增常駐語意化 `<section class="full-guide">` 與對應樣式，覆蓋注音、Shift 英文字母、Caps Lock、Emoji / 標點、F9 對應的繁簡切換說明、Option 刪除學習，以及 localStorage 僅保存在本機的行為。
  - in-canvas 說明與底部狀態列加入 `` ` Emoji``、`' 標點` 與 `Esc` 關閉特殊面板提示。
- 更新 `Tests/test_html_special_candidates_static.py`
  - 新增 canvas render / pointerup 契約。
  - 新增頁底完整說明與頂部 note 文案契約，防止舊的「送出未確認中文」說法回歸。

## RED / GREEN 指令輸出摘要

- RED
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`FAILED (failures=2)`
  - 失敗點：
    - 缺少 `<section class="full-guide" aria-labelledby="full-guide-title">`
    - `render()` 尚未包含 `const visible=candidatePageSize();`
- GREEN
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`Ran 7 tests ... OK`

## 完整驗證

- `python3 Tests/test_html_special_candidates_static.py`
  - `Ran 7 tests ... OK`
- `python3 Tests/test_html_shift_english_static.py`
  - `test_html_shift_english_static: OK`
- `python3 Tests/test_html_native_parity_static.py`
  - `Ran 4 tests ... OK`
- `./run_core_tests.sh`
  - native C core、HTML static、OpenCC、quick-help、learning、跨平台靜態檢查全部通過
  - 結尾：`Candidate caret, Taiwan dictionary, OpenCC tw2s, composition quality, quick-help, and first-tone regression tests: OK`
- `git diff --check`
  - exit 0
- 視覺檢查
  - 由於 `file://` 受 in-app browser URL policy 阻擋，改以暫時性的 `Docs/Reference` 限縮 localhost 服務做檢查。
  - 檢查結果：
    - canvas 高度 `1145`
    - `guideBelowCanvas: true`
    - guide 標題順序為 `完整使用說明 / 注音與候選 / 中英切換與快捷鍵 / Emoji、標點與個人學習`
    - note 含 `取消未確認注音`，不含 `送出未確認中文`
    - Emoji 50 格面板展開後，下方仍可見鍵盤與控制列，未被面板覆蓋

## Commit

- `914de85` — `docs: add HTML input guide`

## 已知疑慮

- Canvas 內部狀態封裝在 IIFE 中，瀏覽器視覺檢查能直接確認的是版面、guide 位置與特殊面板高度；`Esc` 關閉後回到原注音候選的行為，這次主要依賴既有 `closeSpecialCandidates()` / keyboard static regression 來驗證，而不是 DOM 層級直接讀狀態。

---

## Review Fix Round 2（2026-08-17）

### 變更

- 更新 `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`
  - `moveCandidateGrid()` 在特殊候選模式固定以 10 格做上下移動，普通模式保留既有 `candidatePageSize()/2` 行距。
  - `chooseSelectedCandidate()` 改為在特殊候選模式下重試 `stagePunctuation(item)`，可連續消耗多段一般候選，直到成功把 Emoji / 標點接成 pending punctuation；若無法前進則恢復 `specialMode` 與選取位置並回傳 `false`。
  - `switchInputMode()` 現在會清掉 `specialMode` 與選取索引，避免單按 Shift 後留下特殊 50 格面板。
  - 更新頂部 note 與頁底 guide，明確說明單按 Shift 會先送出已確認 pending、清除未確認 composition / 一般候選再切換；Shift+英文字母會保留已確認、取消未確認並直接輸入英文。
- 更新 `Tests/test_html_special_candidates_static.py`
  - 新增特殊模式上下移動必須是 10 格的契約。
  - 新增 `chooseSelectedCandidate()` 需重試 punctuation staging、且在失敗時恢復特殊面板的契約。
  - 新增 Shift 說明文案必須反映 pending / composition 真實行為，且不得回退成「只切換」說法。
- 更新 `Tests/test_html_shift_english_static.py`
  - 新增 `switchInputMode()` 必須清除 `specialMode` 的契約。

### RED / GREEN 指令輸出摘要

- RED
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`FAILED (failures=3)`
  - 失敗點：
    - `moveCandidateGrid()` 尚未改成 `state.specialMode ? 10 : ...`
    - `chooseSelectedCandidate()` 尚未保留／恢復特殊面板與重試 staging
    - Shift 文案仍是舊的「只切換」敘述
- RED
  - `python3 Tests/test_html_shift_english_static.py`
  - 結果：`AssertionError`
  - 失敗點：`switchInputMode()` 尚未清除 `specialMode`
- GREEN
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`Ran 9 tests ... OK`
- GREEN
  - `python3 Tests/test_html_shift_english_static.py`
  - 結果：`test_html_shift_english_static: OK`

### 本輪完整驗證

- `python3 Tests/test_html_special_candidates_static.py`
  - `Ran 9 tests ... OK`
- `python3 Tests/test_html_shift_english_static.py`
  - `test_html_shift_english_static: OK`
- `python3 Tests/test_html_native_parity_static.py`
  - `Ran 4 tests ... OK`
- `./run_core_tests.sh`
  - native C core、HTML static、OpenCC、quick-help、learning、跨平台靜態檢查全部通過
  - 其中包含本輪擴充後的 `test_html_special_candidates_static.py`
  - 結尾：`Candidate caret, Taiwan dictionary, OpenCC tw2s, composition quality, quick-help, and first-tone regression tests: OK`
- `git --no-pager diff --check`
  - exit 0

### 本輪已知疑慮

- 這一輪新增的是靜態回歸契約，能直接防住 reviewer 指出的四個具體邏輯回退；但 `chooseSelectedCandidate()` 的多段 composition 消耗仍是透過原有 `commitCandidate()` / `stagePunctuation()` 協作完成，沒有再額外引入新的 runtime harness。
