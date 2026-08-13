# 真實游標候選框與 Shift 英文輸入設計

## 目標

修正候選框未在組字游標右上方顯示的問題，並在中文模式提供暫時 Shift 英文輸入。

## 候選框

- `clientRect:` 以目前組字字串的長度向輸入 client 查詢 `firstRectForCharacterRange:`，取得 marked text 結尾的真實游標矩形。
- client 未提供有效矩形時才回退使用滑鼠位置。
- 候選框以真實游標矩形的右上方 6 px 為固定錨點；不足以顯示時裁切候選框，不會移回或覆蓋游標。

## Shift 英文輸入

- 僅在中文模式、沒有 Command／Option／Control 的情況下生效。
- Shift 加可列印英文字母時，插入 `event.characters` 的英文文字到 client，不轉為注音、不切換中英模式。
- Shift 加數字保持原有選字行為；Shift 加標點保持原有中文標點行為；單獨 Shift 仍維持中英切換。

## 驗證

- 自動檢查真實 marked-text 游標範圍、右上錨點與 Shift 英文插入分支。
- 執行 Objective-C++ 編譯與既有核心測試。

## 不在範圍

- 不變更候選字選擇邏輯、輸入法狀態、bundle ID 或圖示。
