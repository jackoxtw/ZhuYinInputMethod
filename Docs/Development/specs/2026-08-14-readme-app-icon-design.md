# README 應用程式圖示設計

## 目標

讓 GitHub README 的開頭立即呈現逐音輸入法的既有應用程式圖示。

## 設計

- 沿用版本控制中的 `icon/icon.png`，不新增或下載任何圖檔。
- 在 README 主標題前插入置中的 HTML 圖片，寬度固定為 96px。
- 使用相對路徑，讓 GitHub、專案下載副本與本機 Markdown 預覽都能解析。

## 範圍與驗證

- 僅修改 `README.md` 的開頭；不改應用程式、建置腳本或 Release。
- 確認圖片路徑存在、Markdown 結構正常，並以 `git diff --check` 驗證。
