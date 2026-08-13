# Simplified Output Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在原生逐音輸入法候選窗加入繁／簡輸出切換，並保存最後選擇。

**Architecture:** `ZYInputController` 是輸出 script 狀態唯一來源；`ZYCandidatePanel` 只顯示狀態與送出 toggle delegate callback。真正繁→簡仍只發生在既有 `learnAndCommit:` 的最終 `insertText:` 前。

**Tech Stack:** Objective-C++、AppKit、InputMethodKit、NSUserDefaults、既有 ZYConversion/t2s.bin。

## Global Constraints
- 候選與學習資料維持繁體。
- 簡體轉換只作用於最終 commit。
- 新安裝預設繁體。
- 不新增第三方 runtime dependency。

---

### Task 1: 候選窗繁／簡按鈕

**Files:**
- Modify: `App/ZYCandidatePanel.h`
- Modify: `App/ZYCandidatePanel.mm`
- Test: `Tests/test_script_toggle_static.py`

**Interfaces:**
- Consumes: `updateCandidates:count:selected:chinese:simplified:` 的 `simplified`。
- Produces: `-candidatePanelToggleScript` delegate callback。

- [ ] **Step 1: Write failing test** — assert delegate method、48×32 status button rendering、hit testing callback。
- [ ] **Step 2: Run test and verify RED.**
- [ ] **Step 3: Implement minimal panel drawing and hit testing.**
- [ ] **Step 4: Run test and verify GREEN.**

### Task 2: 狀態保存與 controller callback

**Files:**
- Modify: `App/ZYInputController.mm`
- Test: `Tests/test_script_toggle_static.py`

**Interfaces:**
- Consumes: `candidatePanelToggleScript`。
- Produces: `_simplified` persisted in `NSUserDefaults` key `ZYOutputSimplified`。

- [ ] **Step 1: Extend failing test** — init loads default and toggle writes it。
- [ ] **Step 2: Run test and verify RED.**
- [ ] **Step 3: Implement load/save and delegate callback.**
- [ ] **Step 4: Run test and verify GREEN.**

### Task 3: Regression verification and packaging

**Files:**
- Modify: `run_core_tests.sh` to include the new static test.

- [ ] **Step 1: Run all core/static regression tests.**
- [ ] **Step 2: Build final ZIP preserving executable bits.**
- [ ] **Step 3: Extract final ZIP into a clean directory and rerun all portable tests.**
