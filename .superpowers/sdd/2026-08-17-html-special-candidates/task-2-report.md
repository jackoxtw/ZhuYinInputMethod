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

---

## Final Fix Wave（2026-08-17）

### 變更

- 更新 `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`
  - virtual Canvas 注音鍵 `pointerup` 的 `symbol` 分支改為先 `closeSpecialCandidates()` 再 `handleSymbol(hit.value)`，確保從 Emoji / 標點面板點回注音鍵時會立即退出特殊模式並回到一般候選路徑。
  - Shift 標點分支改為在 `stagePunctuation(zhPunct)` 前先 `closeSpecialCandidates()`，讓特殊面板開啟時的 Shift 標點流程和 native parity 一致。
  - `chooseSelectedCandidate()` 在「composition 為空且沒有 pending parts」時，特殊 Emoji / 標點不再直接寫入 `committed`，而是最小幅度地改成 `appendPendingPunctuationPart(...)` 建立待確認 punctuation piece；按 Enter 後才真正送出。一般空白標點分支仍維持原本行為。
  - 調整頁底 guide 文案，移除「Space 可直接選一般候選」的錯誤宣稱，改為精確描述目前行為：一般中文模式下，Space 只處理一聲／分音；特殊候選仍可用 Space 選取。
  - `.full-guide` 新增 `box-sizing:border-box`，修正 390px 手機 viewport 下 content-box 加 padding 造成的水平溢位。
- 更新 `Tests/test_html_special_candidates_static.py`
  - 新增 virtual Canvas `symbol` 點擊必須先關閉 `specialMode` 的契約。
  - 新增 Shift 標點路徑必須先關閉 `specialMode` 的契約。
  - 新增特殊候選在空 composition / pending 時必須建立 pending punctuation、不可直接 committed 的契約。
  - 新增 guide 文案與 `.full-guide` mobile overflow 修正的回歸檢查。

### 特殊空狀態選取的最終行為

- 當 `composition === ''` 且 `pendingParts.length === 0` 時，選取特殊 Emoji / 標點會走：
  - `state.pendingParts = appendPendingPunctuationPart(state.pendingParts, item)`
  - `refreshCandidates()`
  - `return true`
- 也就是特殊項目會先留在 pending punctuation，而不是直接進入 `state.committed`；之後需由 Enter（或既有送出流程）完成真正送出。

### RED / GREEN 指令輸出摘要

- RED
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`FAILED (failures=6)`
  - 失敗點：
    - virtual Canvas `symbol` 分支尚未先 `closeSpecialCandidates()`
    - Shift 標點分支尚未先關閉特殊模式
    - 特殊候選空狀態仍會直接 committed
    - guide 仍錯誤宣稱一般 Space 可直接選候選
    - `.full-guide` 尚未套用 `box-sizing:border-box`
- GREEN
  - `python3 Tests/test_html_special_candidates_static.py`
  - 結果：`Ran 13 tests ... OK`
- GREEN
  - `python3 Tests/test_html_shift_english_static.py`
  - 結果：`test_html_shift_english_static: OK`

### 本輪完整驗證

- `python3 Tests/test_html_special_candidates_static.py`
  - `Ran 13 tests ... OK`
- `python3 Tests/test_html_shift_english_static.py`
  - `test_html_shift_english_static: OK`
- `python3 Tests/test_html_native_parity_static.py`
  - `Ran 4 tests ... OK`
- `./run_core_tests.sh`
  - 驗證 native C core、HTML static、OpenCC、quick-help、learning、跨平台靜態檢查與本輪特殊候選回歸測試
  - 結尾摘要：`Candidate caret, Taiwan dictionary, OpenCC tw2s, composition quality, quick-help, and first-tone regression tests: OK`
- `git --no-pager diff --check`
  - exit 0

### Canvas virtual key / Shift punctuation 驗證方式

- 以 `Tests/test_html_special_candidates_static.py` 的靜態契約直接驗證：
  - virtual Canvas 注音鍵分支必須包含 `closeSpecialCandidates();handleSymbol(hit.value);`
  - Shift 標點分支必須包含 `closeSpecialCandidates();stagePunctuation(zhPunct);return;`
- 以同檔回歸測試驗證空狀態特殊選取必須包含 `appendPendingPunctuationPart(...)`，並禁止 `state.committed+=item` 的直接送出回退。

### 本輪已知疑慮

- 本輪維持最小改動策略，空狀態特殊選取的 pending 行為是透過 `chooseSelectedCandidate()` 的特殊分支補齊，而不是重寫 `stagePunctuation()` 的一般空白標點語意；這樣能保留既有普通標點分支，但仍主要仰賴靜態契約而非額外 runtime harness 來防回退。
