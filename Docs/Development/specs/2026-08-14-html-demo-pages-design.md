# HTML 線上試用頁設計

## 目標

將既有 Canvas 單檔原型部署為 GitHub Pages，並從 README 提供一般使用者可直接開啟的試用入口。

## 設計

- 保留原型唯一來源：`Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`。
- GitHub Actions 在推送 `main` 時將該檔案複製為 Pages artifact 的 `index.html`，不在儲存庫新增 2.5 MB 的重複檔案。
- README 使用 `https://jackoxtw.github.io/ZhuYinInputMethod/` 作為「線上試用 HTML 原型」連結，並標示它是 Canvas 原型、非可安裝的 macOS 輸入法。
- 工作流程只取得 GitHub Pages 部署所需的 `pages: write` 與 `id-token: write` 權限。

## 範圍與驗證

- 新增一個 Pages 部署工作流程，並修改 README 開頭的試用入口。
- 推送後在 GitHub Pages 設定中使用 GitHub Actions 作為來源。
- 以部署工作流程成功與已發布頁面的 HTTP 回應驗證；不變更儲存庫可見性。
