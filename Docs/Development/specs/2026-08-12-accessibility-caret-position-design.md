# 輔助使用游標定位設計

## 目標

讓逐音輸入法的自訂候選框在所有可支援的 macOS 文字欄位中跟隨實際文字插入點，不再固定於螢幕左下角。

## 設計

- 建立獨立的 Accessibility caret helper。
- helper 從 system-wide AX element 取得目前 focused UI element、selected text range 和該範圍的 bounds。
- 將 Accessibility 的螢幕座標轉換為 AppKit 螢幕座標，支援依顯示器做局部座標轉換。
- `clientRect:` 優先使用 AX rect；AX 未授權、元素不支援或回傳無效 rect 時，使用目前 client rect；client rect 同樣無效時，使用滑鼠位置。
- 首次需要 AX 時觸發系統授權提示；使用者可在「系統設定 → 隱私權與安全性 → 輔助使用」允許逐音輸入法。

## 整合

- 編譯與手動建置腳本新增 ApplicationServices framework。
- 候選框的既有右上方 6px 規則不變。

## 驗證

- 靜態檢查 AX focused element、selected range、bounds-for-range、坐標轉換與滑鼠後備均存在。
- 編譯 helper 與輸入控制器，並執行核心測試。

## 不在範圍

- 不變更輸入法的選字、候選框外觀、圖示、bundle ID 或快捷鍵行為。
