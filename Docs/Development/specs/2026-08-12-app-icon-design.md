# 逐音輸入法 App 圖示設計

## 目標

使用專案的 `icon/icon.png` 作為唯一圖示來源，讓逐音輸入法在 Finder 與 macOS 輸入來源清單使用同一個 App 圖示。

## 實作範圍

- 建置腳本從 1094×1094 RGBA PNG 產生 macOS 標準尺寸的 `AppIcon.icns`。
- 產出的 `.icns` 放入 App bundle 的 `Contents/Resources`。
- `Info.plist` 指定 `CFBundleIconFile` 為 `AppIcon.icns`，且輸入模式的選單與候選面板圖示都參照它。
- 建置時移除圖示來源與產物的延伸屬性，避免 Finder metadata 再次造成 codesign 失敗。
- 靜態檢查確認圖示來源、轉檔指令、bundle 內容與 Info.plist 參照存在。

## 不在範圍

- 不變更目前 `icon/icon.png` 的設計。
- 不變更 bundle ID、輸入來源 ID 或輸入引擎行為。

## 錯誤處理

若 PNG 不存在、`iconutil` 無法建立 `.icns`，或圖示未成功放進 bundle，腳本因 `set -euo pipefail` 停止，避免安裝缺少圖示的 App。
