# 清除學習資料設計規格

## 目標

在候選窗右側「說明」按鈕下方新增「清除學習」按鈕，讓使用者可清除逐音輸入法累積的個人學習資料。清除屬於不可復原的破壞性操作，必須先經過警告確認；預設按鈕必須是「取消」，避免按 Enter 誤刪。

## 使用者介面

右側控制區由上到下為：繁／簡、說明、清除學習。為完整容納第三個按鈕，候選面板最小高度由 88pt 提高到 110pt；一般候選內容與 10／5／4 欄自適應排版維持不變。

點擊「清除學習」後顯示 NSAlert warning：

- 標題：「確定要清除學習資料嗎？」
- 說明：「將清除逐音輸入法已學習的詞彙與選字偏好，包括最近使用、常用詞頻、Query Preferred 與自訂學習詞組。內建詞庫、台灣詞庫、繁簡設定、Emoji、標點與其他設定不受影響。此操作無法復原。」
- 第一個（預設）按鈕：「取消」
- 第二個按鈕：「清除學習資料」

只有第二個按鈕才執行清除。成功後顯示「學習資料已清除。」；失敗則顯示「無法清除學習資料」，且不得把記憶體中的學習狀態誤清空。

## 資料範圍

清除：

- `learning_A.dat`
- `learning_B.dat`
- Runtime 記憶體內的 word learning
- query preference / query frequency
- phrase learning
- recent-use / frequency 統計
- 已學詞縮寫召回依據

保留：

- `dictionary.bin`
- `Resources/brand_words.csv` 與「逐音輸入法」品牌詞
- libchewing 台灣詞庫 overlay
- OpenCC `t2s.bin`
- 繁／簡設定
- Emoji 與中文標點
- 其他 UI 偏好

## 架構

`ZYCandidatePanel` 只負責繪製按鈕與把點擊事件交給 delegate；不直接碰檔案或 Runtime。`ZYInputController` 負責顯示警告與結果訊息，確認後呼叫 `ZYRuntimeClearLearning()`。Runtime 先確認 A/B snapshot 都可移除（不存在視為成功），全部成功後才重建空的 `ZYLearning`，因此清除立即生效且 shutdown 不會把舊資料重新寫回。

## 安全性與邊界

- Enter 在警告視窗預設執行「取消」，不是刪除。
- 取消不改動任何記憶體或磁碟學習資料。
- 清除不會清掉目前正在組字的 composition；使用者關閉警告後仍可繼續輸入。
- 若任一 snapshot 刪除失敗，Runtime 回報失敗並保留目前記憶體中的學習狀態。
- 學習資料不存在時執行清除視為成功。
