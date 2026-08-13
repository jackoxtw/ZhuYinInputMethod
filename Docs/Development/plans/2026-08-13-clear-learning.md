# 清除學習資料 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在候選窗加入需二次警告確認的「清除學習」功能，立即清空磁碟與記憶體學習資料而保留所有內建功能與設定。

**Architecture:** `ZYCandidatePanel` 新增按鈕與 delegate event；`ZYInputController` 顯示 NSAlert 並只在第二個明確確認按鈕後呼叫 Runtime；`ZYRuntimeClearLearning()` 負責刪除 A/B snapshots 並重設 `ZYLearning`。Core 新增可單元測試的 `zy_learning_reset()`，不負責檔案路徑。

**Tech Stack:** Objective-C++ / AppKit / InputMethodKit / C99 core / Python static regression tests.

## Global Constraints

- 以 v0.1.22 / build 23 為基底。
- 不刪除 dictionary、OpenCC、brand words、繁簡設定、Emoji、標點或其他 UI 設定。
- 警告視窗預設動作必須是取消；只有第二個明確按鈕可刪除。
- 清除成功必須立即影響目前 Runtime，不需重新啟動輸入法。
- 清除失敗不得把記憶體中的學習狀態清空。

---

### Task 1: Core learning reset

**Files:**
- Modify: `Core/ZYLearning.h`
- Modify: `Core/ZYLearning.c`
- Modify: `Tests/test_learning.c`

**Interfaces:**
- Produces: `void zy_learning_reset(ZYLearning *l, uint64_t now_seconds)`，清空 persistent learning、generation、dirty count 並更新 flush 時間。

- [ ] **Step 1:** 在 `Tests/test_learning.c` 先建立有 word/query/phrase 資料的 learning，呼叫 `zy_learning_reset` 後驗證 clock、counts、phrases、generation、dirty 都歸零。
- [ ] **Step 2:** 執行 `./run_core_tests.sh`，確認因缺少 API 而失敗。
- [ ] **Step 3:** 實作 `zy_learning_reset`，共用 `zy_learning_init` 的清空語意。
- [ ] **Step 4:** 重跑 core tests 確認通過。

### Task 2: Runtime disk + memory clear

**Files:**
- Modify: `App/ZYRuntime.h`
- Modify: `App/ZYRuntime.mm`
- Create: `Tests/test_clear_learning_static.py`

**Interfaces:**
- Consumes: `zy_learning_reset`
- Produces: `BOOL ZYRuntimeClearLearning(void)`

- [ ] **Step 1:** 靜態測試要求 Runtime API、`learning_A.dat` / `learning_B.dat` 刪除路徑、成功後 reset、失敗時不 reset。
- [ ] **Step 2:** 執行測試確認紅燈。
- [ ] **Step 3:** 用 `NSFileManager` 刪除兩個 snapshot；不存在視為成功；兩者成功後呼叫 `zy_learning_reset(&gLearning, now_seconds())`。
- [ ] **Step 4:** 重跑定向測試。

### Task 3: Candidate panel button and destructive confirmation

**Files:**
- Modify: `App/ZYCandidatePanel.h`
- Modify: `App/ZYCandidatePanel.mm`
- Modify: `App/ZYInputController.mm`
- Modify: `Tests/test_clear_learning_static.py`

**Interfaces:**
- Produces delegate: `candidatePanelRequestClearLearning`

- [ ] **Step 1:** 靜態測試要求「清除學習」位於「說明」下方、面板 min height >= 110、mouse hit-test、warning alert、第一按鈕取消、第二按鈕清除，以及只有 `NSAlertSecondButtonReturn` 才呼叫 Runtime。
- [ ] **Step 2:** 執行測試確認紅燈。
- [ ] **Step 3:** 實作按鈕、delegate、NSAlert 與成功／失敗提示。
- [ ] **Step 4:** 重跑 quick-help、adaptive-layout 與 clear-learning tests。

### Task 4: Release integration

**Files:**
- Modify: `README.md`
- Modify: `App/Info.plist`
- Modify: `run_core_tests.sh`

**Interfaces:**
- Produces: v0.1.23 / build 24 release.

- [ ] **Step 1:** README 記錄清除範圍、警告確認及不受影響項目。
- [ ] **Step 2:** 將版本升為 0.1.23、build 24，並把新 regression test 加入總測試。
- [ ] **Step 3:** 跑完整 `./run_core_tests.sh`、Objective-C++ static checks、installer shell syntax。
- [ ] **Step 4:** 打 ZIP，解壓到全新目錄後重跑完整驗證與權限檢查。
