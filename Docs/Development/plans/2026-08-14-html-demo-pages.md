# HTML 線上試用頁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將既有 Canvas HTML 原型發布成 GitHub Pages，並在 README 提供公開試用入口。

**Architecture:** GitHub Actions 從 `Docs/Reference` 的單一原型檔建立最小 Pages artifact，將它命名為 `index.html` 後部署。README 連結固定指向 GitHub Pages 專案網址。

**Tech Stack:** GitHub Actions、GitHub Pages、GitHub Flavored Markdown。

## Global Constraints

- 不新增或複製 2.5 MB 原型 HTML；來源維持 `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`。
- 不變更儲存庫可見性。
- README 明確將線上版本稱為 Canvas 原型。

---

### Task 1: 建立 GitHub Pages 部署工作流程

**Files:**
- Create: `.github/workflows/deploy-html-demo.yml`
- Test: 工作流程 YAML 與原型檔路徑

**Interfaces:**
- Consumes: `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`
- Produces: GitHub Pages 的 `/index.html`

- [x] **Step 1: 建立 workflow**

使用 `actions/configure-pages`、`actions/upload-pages-artifact` 與 `actions/deploy-pages`；以 shell 建立 `_site/index.html` 與 `.nojekyll`。

- [x] **Step 2: 驗證 workflow 引用**

Run: `rg -n -F '台灣注音輸入法_Canvas_單檔版(20260812-065531).html' .github/workflows/deploy-html-demo.yml`

Expected: exit code 0。

### Task 2: 加入 README 試用入口

**Files:**
- Modify: `README.md:1-12`
- Test: README 中的 GitHub Pages URL

**Interfaces:**
- Consumes: `https://jackoxtw.github.io/ZhuYinInputMethod/`
- Produces: 使用者可辨識的「線上試用 HTML 原型」連結

- [x] **Step 1: 加入試用連結與原型說明**

在主標題前的圖示區塊中加入連結，文字說明為 Canvas 原型。

- [x] **Step 2: 驗證 README 與格式**

Run: `git diff --check && rg -n -F 'https://jackoxtw.github.io/ZhuYinInputMethod/' README.md`

Expected: exit code 0。

- [ ] **Step 3: 推送並確認 GitHub Pages 發布**

推送 `main` 後，於 GitHub Pages 設定選擇 GitHub Actions，確認部署工作流程成功及頁面可開啟。
