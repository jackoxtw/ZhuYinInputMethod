# Candidate Panel 記憶體分段診斷設計

## 目標

在不終止 `ZhuYinInputMethod`、不破壞 InputMethodKit active session 的前提下，把候選窗造成的瞬間 RSS 峰值拆成「建構、候選資料/排版、空白視窗顯示、完整繪製」四段。

## 架構

`MemoryDiagnosticMode` 改為每次 `refreshCandidates:` 都透過 `CFPreferences` 即時讀取。模式變更時釋放既有 Candidate Panel，下一個按鍵依新模式建立乾淨測試狀態。

模式：
- 1：setMarkedText only。
- 2：+ Runtime lookup。
- 4：+ 建立 Candidate Panel，不填內容、不顯示。
- 5：+ 真實候選轉換/排版，不顯示。
- 6：+ 顯示空白 Candidate Panel。
- 3：完整正常候選窗。
- 0：正式正常模式。

## 安全性

診斷工具不得使用 `killall`/`pkill`，不得寫 `/tmp` 或診斷 log。測試完成自動刪除 `MemoryDiagnosticMode`；下一個按鍵回到 Mode 0。
