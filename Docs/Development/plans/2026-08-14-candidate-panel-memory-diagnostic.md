# Candidate Panel Memory Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 安全地把 Candidate Panel 記憶體峰值拆成 Mode 4/5/6，且切換模式不重啟 InputMethodKit。

**Architecture:** `ZYInputController` 每次刷新即時同步 `CFPreferences`。模式變更先釋放舊 Panel，再依模式停在 panel 建構、候選準備、空白顯示或完整顯示的不同邊界。

**Tech Stack:** Objective-C++ / InputMethodKit / AppKit / CoreFoundation / zsh static test harness

## Global Constraints

- 不使用 `killall` 或 `pkill` 切換診斷模式。
- 不寫診斷 log。
- Mode 0/3 正常功能不變。
- 不修改詞庫、Runtime 排序、Composer、學習或候選數量。

---

### Task 1: Live diagnostic modes

**Files:**
- Modify: `App/ZYInputController.mm`
- Test: `Tests/test_memory_diagnostic_modes_static.py`

- [x] 先新增 Mode 4/5/6 與 live preference 的失敗測試。
- [x] 用 `CFPreferencesAppSynchronize` + `CFPreferencesCopyAppValue` 即時讀模式。
- [x] 實作 panel construct / prepare no show / blank visible 三個邊界。
- [x] 驗證靜態測試轉綠。

### Task 2: Safe macOS test command

**Files:**
- Create: `Tools/逐音輸入法_候選視窗記憶體測試.command`
- Test: `Tests/test_memory_diagnostic_command_static.py`

- [x] 先新增禁止 process termination 的失敗測試。
- [x] 依序量測 1/2/4/5/6/3，使用 RSS 取樣但不重啟輸入法。
- [x] 完成後刪除 defaults key。
- [x] 驗證測試腳本不吞掉互動提示。

### Task 3: Release metadata and regression

**Files:**
- Modify: `App/Info.plist`
- Modify: `README.md`
- Modify: `run_core_tests.sh`

- [x] 升版至 v0.1.41 / build 42。
- [x] README 移除舊版需要 killall 的操作說明，記錄安全測試流程。
- [x] 跑完整回歸與最終 ZIP 解壓驗證。
