# 候選排版移除文字量測設計

## 目標

移除候選準備階段中逐一使用 `NSStringDrawing`／CoreText 量測文字的操作，降低瞬間配置的記憶體峰值。同時保留候選召回、排序、分頁數、面板尺寸、選取與滑鼠操作。

## 範圍

只修改 `ZYCandidateView::prepareCandidateTextLayout`。

- 10 欄候選維持既有字級選擇，並視為單行。
- 5 欄候選維持既有 16pt 字級，並視為單行。
- 4 欄候選改以既有格寬與 UTF-16 字元數做受限估算；長詞會選用既有的 12pt 下限，仍和原本一樣由 `drawRect:` 裁切在格內。
- 繪製仍使用已儲存的字級與垂直位移陣列，因此 `drawRect:` 不會重新量測文字。

## 非目標

- 不修改詞庫、Runtime 查詢、Composer、學習、候選數、分頁數、面板生命週期、backing-store 策略或 caret 查詢。
- 不加入診斷 log、終止程序或磁碟寫入。

## 驗證

新增靜態回歸測試，確認 `ZYCandidatePanel.mm` 不再出現 `boundingRectWithSize:`，且排版仍使用既有 12pt 下限與快取的排版陣列。執行受影響的靜態測試、原生 C 核心測試及 macOS CMake 編譯；最後以編譯出的輸入法重跑安全的六段 RSS 診斷，並以 Mode 5 作為比較重點。
