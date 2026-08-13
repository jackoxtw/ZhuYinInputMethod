# 原生版繁／簡輸出切換設計

## 目標
還原網頁版的「正常注音輸入、候選維持繁體、最終輸出可切換簡體」功能。

## 行為
- 候選窗右側顯示一個 48×32 的「繁／簡」切換按鈕，視覺語意比照網頁版：簡體模式使用高亮底色與白字；繁體模式使用淺色底與深色字。
- 點擊按鈕只改變輸出 script，不改變注音解析、候選字、學習字詞或 preedit。
- Enter 最終 commit 時沿用既有 `ZYRuntimeOutputString(text, simplified)` 做繁→簡轉換。
- 既有輸入法選單「改為簡體輸出／改為繁體輸出」與候選窗按鈕操作同一份狀態。
- 使用 `NSUserDefaults` 儲存 `ZYOutputSimplified`；新安裝預設為繁體，之後沿用最後一次選擇。

## 影響檔案
- `App/ZYCandidatePanel.h/.mm`: 顯示與點擊繁／簡按鈕。
- `App/ZYInputController.mm`: 載入、儲存與同步 `_simplified` 狀態。
- `Tests/test_script_toggle_static.py`: 原生 UI 與 persistence 回歸檢查。

## 不變項
- 不把候選字本身轉成簡體。
- 不把學習詞庫寫成簡體。
- 不改變 `t2s.bin` 格式或轉換演算法。
- 不新增額外快捷鍵。
