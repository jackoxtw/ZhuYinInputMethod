# README 應用程式圖示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GitHub README 開頭顯示專案既有的逐音輸入法應用程式圖示。

**Architecture:** README 以原生 HTML 包住相對路徑的 PNG，取得置中與固定寬度的穩定呈現。僅調整文件開頭，不影響程式、建置或 Release。

**Tech Stack:** GitHub Flavored Markdown、HTML `img`。

## Global Constraints

- 使用現有的 `icon/icon.png`，不新增圖像資產或外部 URL。
- 圖示置於 README 主標題之前，寬度固定為 96px。
- 驗證路徑存在與 `git diff --check` 成功。

---

### Task 1: 加入 README 圖示

**Files:**
- Modify: `README.md:1`
- Test: `README.md` 的圖示路徑與 Markdown 差異檢查

**Interfaces:**
- Consumes: 版本控制中的 `icon/icon.png`
- Produces: README 開頭的置中圖示區塊

- [x] **Step 1: 確認圖示資產存在**

Run: `test -f icon/icon.png`

Expected: exit code 0。

- [x] **Step 2: 在主標題前加入置中圖示**

```html
<p align="center">
  <img src="icon/icon.png" alt="逐音輸入法圖示" width="96">
</p>
```

- [x] **Step 3: 驗證文件變更**

Run: `git diff --check && rg -n -F 'src="icon/icon.png"' README.md`

Expected: exit code 0，且找到圖示元素。

- [x] **Step 4: 提交變更**

```bash
git add README.md
git commit -m "docs: add app icon to readme"
```
