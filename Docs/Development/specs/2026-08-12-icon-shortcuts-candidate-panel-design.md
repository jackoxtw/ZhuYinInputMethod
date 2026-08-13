# 圖示、快捷鍵與候選框位置設計

## 目標

改善逐音輸入法的 macOS 整合：使用專案圖示、讓系統快捷鍵不被輸入法攔截，並讓候選框不遮住組字中的注音。

## 圖示

- 使用 `icon/icon.png` 作為唯一來源，建立標準 `AppIcon.icns` 並放入 App bundle Resources。
- `Info.plist` 以 `CFBundleIconFile` 指定 App 圖示；輸入模式的選單與候選面板圖示也參照 `AppIcon.icns`。
- 建置流程清除圖示與 App bundle 的延伸屬性，避免 codesign 失敗。

## 系統快捷鍵

- 含 `Command`、`Option` 或 `Control` 的 `keyDown` 事件一律回傳 `NO`，交由原本的 macOS App 處理。
- 單獨的 Shift 仍維持現有中英切換；未含上述三個修飾鍵的 Shift 選字仍可使用。

## 候選框位置

- 候選框固定在游標矩形的右上方：左邊緣位於游標右緣外 6 px，下邊緣位於游標上緣外 6 px。
- 候選框的位置限制在目前螢幕的可視範圍；候選框永遠不會覆蓋游標矩形。
- 不再依可用垂直空間切換到游標上方或下方。

## 驗證

- 新增或擴充自動檢查，涵蓋 `.icns` 產生與 bundle 參照、修飾鍵事件直通、候選框右上方定位的幾何規則。
- 執行現有核心測試與 macOS Objective-C++ 編譯檢查。

## 不在範圍

- 不變更圖示設計、bundle ID、輸入來源 ID、候選字排序或輸入引擎行為。
