# 候選排版移除文字量測實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目標：** 移除候選排版每鍵觸發的 CoreText 文字量測，降低 Mode 5 的瞬間記憶體配置，且不改變候選功能。

**架構：** `ZYCandidateView` 繼續在候選更新時預先填入 `_textFontSizes` 和 `_textVerticalOffsets`，而 `drawRect:` 只讀取這兩組資料。排版準備改為固定單行字型 metrics 與 4 欄長詞的保守字元數估算，完全不進入 `NSStringDrawing` 量測。

**技術：** Objective-C++、AppKit、既有 Python 靜態回歸測試、CMake。

## 全域限制

- 不修改詞庫、Runtime、Composer、Learning、候選數、分頁數、面板生命週期或 caret 查詢。
- 不加入 log、程序終止或診斷檔案寫入。
- 10 欄與 5 欄候選維持既有字級；4 欄長詞最低為 12pt，並維持格內裁切。

---

### Task 1：以無量測排版保護候選面板

**檔案：**
- 修改：`Tests/test_peak_memory_static.py`
- 修改：`App/ZYCandidatePanel.mm`

**介面：**
- 使用：`- (void)prepareCandidateTextLayout` 寫入 `_textFontSizes[50]` 和 `_textVerticalOffsets[50]`。
- 產出：候選面板的準備與繪製路徑皆不呼叫 `boundingRectWithSize:`。

- [ ] **Step 1：寫入失敗的回歸測試**

在 `Tests/test_peak_memory_static.py` 增加整個候選面板檔案不得出現 `boundingRectWithSize:` 的斷言；目前它會因 prepare 階段兩處量測呼叫而失敗。

- [ ] **Step 2：執行測試並確認失敗**

執行：`python3 Tests/test_peak_memory_static.py`

預期：以「candidate panel must not measure candidate text」失敗。

- [ ] **Step 3：實作最小無量測排版**

在 `prepareCandidateTextLayout` 移除所有 `boundingRectWithSize:` 分支：10／5 欄以既有字級與 `NSFont` metrics 計算垂直置中；4 欄只在預估文字寬度超過文字格寬時降為 12pt。保留 12 至 18pt 的有效範圍及 `_textFontSizes`／`_textVerticalOffsets` 的寫入。

- [ ] **Step 4：執行目標測試並確認通過**

執行：`python3 Tests/test_peak_memory_static.py && python3 Tests/test_candidate_grow_only_static.py && python3 Tests/test_candidate_idle_release_static.py`

預期：三項皆通過。

### Task 2：編譯與核心回歸

**檔案：**
- 驗證：`CMakeLists.txt`、`run_core_tests.sh`

- [ ] **Step 1：執行核心與候選排版回歸**

執行：`./run_core_tests.sh`

預期：所有與本次變更無關的既有失敗會明確記錄；所有觸及候選排版的測試均通過。

- [ ] **Step 2：執行 macOS CMake 編譯**

執行：`cmake -S . -B build && cmake --build build`

預期：Objective-C++ 候選面板編譯成功。

- [ ] **Step 3：實機比較**

以新建置的輸入法執行 `Tools/逐音輸入法_候選視窗記憶體測試.command`，記錄 Mode 1／2／4／5／6／3，將 Mode 5 與 v0.1.41 的 92.6 MB 比較。
