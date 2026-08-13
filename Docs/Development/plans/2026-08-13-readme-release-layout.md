# README 與發行目錄整理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重寫逐音輸入法 README 並以低風險方式整理非建置資料夾。

**Architecture:** 保持所有建置相關目錄與路徑不變，只移動舊網頁參考檔與開發紀錄。以靜態回歸測試鎖住 README 必要章節與發行目錄布局。

**Tech Stack:** Markdown、Bash、Python 3、既有 C99/Objective-C++ 專案測試。

## Global Constraints

- 正式名稱固定為「逐音輸入法」。
- 不搬動 App/Core/Resources/Tools/Tests/Licenses。
- build_and_install.command、uninstall.command、run_core_tests.sh 必須維持可執行。
- Legacy HTML 移至 Docs/Reference/。
- 開發紀錄移至 Docs/Development/。

---

### Task 1: 鎖定 README 與目錄布局

**Files:**
- Create: `Tests/test_release_structure.py`

**Interfaces:**
- Consumes: 專案根目錄、README.md、Docs 目錄。
- Produces: 發行結構靜態回歸測試。

- [ ] Step 1: 建立會因目前舊布局而失敗的測試。
- [ ] Step 2: 執行 `python3 Tests/test_release_structure.py`，確認因根目錄 HTML 與缺少新 README 章節而失敗。
- [ ] Step 3: 完成 Task 2 後重新執行，確認通過。

### Task 2: 重寫 README 並整理非建置資料

**Files:**
- Modify: `README.md`
- Move: `台灣注音輸入法_Canvas_單檔版(20260812-065531).html` → `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`
- Move: `docs/superpowers/specs/*` → `Docs/Development/specs/`
- Move: `docs/superpowers/plans/*` → `Docs/Development/plans/`

**Interfaces:**
- Consumes: 現有功能、安裝腳本與測試行為。
- Produces: 使用者/開發者共用的 README 與乾淨根目錄。

- [ ] Step 1: 依設計重寫 README。
- [ ] Step 2: 建立 `Docs/Reference`、`Docs/Development` 並移動檔案。
- [ ] Step 3: 移除空的舊 `docs/`。
- [ ] Step 4: 執行 release structure 測試。

### Task 3: 完整驗證與重新打包

**Files:**
- Verify: entire project

**Interfaces:**
- Consumes: 整理後專案。
- Produces: 可交付 ZIP。

- [ ] Step 1: 執行 `./run_core_tests.sh`。
- [ ] Step 2: 執行 `bash Tests/check_objcpp_linkage_and_panel.sh` 與 `bash Tests/test_install_destinations.sh`。
- [ ] Step 3: 執行 `bash -n build_and_install.command uninstall.command run_core_tests.sh`。
- [ ] Step 4: 確認三個 shell 入口權限為 755。
- [ ] Step 5: 打包 ZIP，重新解壓後再次執行相同驗證。
