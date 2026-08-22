# 候選框外掛組字顯示設計

## 目標

未完成的注音與已選但尚未最終確認的中文，僅顯示在逐音輸入法候選框頂端；不再以 InputMethodKit 的 `setMarkedText:` 顯示在目前 App 的文字游標旁。最後按 Enter 完成送出時，才以 `insertText:` 寫入最終中文。

此設計降低未正確處理 IME composition 的聊天網頁把 `ㄋㄧㄏㄠˇ` 或尚未送出的組字內容直接送出的機率。

## 範圍與不變項目

- 僅修改 macOS 原生輸入法的組字呈現與候選面板布局。
- 保留既有候選排序、學習、繁簡輸出、Emoji／標點候選、快捷鍵與最終 `insertText:` 行為。
- 不修改第三方網頁，也不要求輸入監控或輔助使用權限。
- 不保證修正第三方網頁所有不當的 Enter 事件；目標是避免該網頁在 Enter 的 `keydown` 階段讀到未確認注音。

## 顯示與資料流

1. `ZYInputController` 仍以既有 `preeditText` 產生待確認文字：先接已選候選的 `piecesText`，再接未完成注音 `_composition`。
2. 當待確認文字不為空時，controller 清除 client 的 marked text，而不將 `preeditText` 傳入 App；候選框頂端以獨立 header 顯示該文字。
3. 一般候選仍顯示在 header 下方；header 固定只顯示一行，過長時採尾端截斷，避免候選框高度隨每次輸入大幅變動。
4. 已選中文字但尚未按 Enter 時，即使沒有剩餘注音候選，候選框仍保留最小高度顯示 header，讓使用者看見待確認內容，而不是讓畫面完全空白。
5. 最後按 Enter 時維持 `learnAndCommit:`：只在此時以 `insertText:` 輸出繁／簡轉換後的中文，清空內部 pending state 與候選框。

範例：輸入並選出「你好」後繼續鍵入未完成注音，候選框顯示：

```text
你好ㄋㄧㄏㄠˇ
[你] [妳] [倪] …
```

網頁文字欄位在此期間不顯示上列內容；下一次 Enter 的網頁 `keydown` 因而無法讀到未確認注音。

## 元件調整

### `ZYInputController`

- 將 inline marked text 更新改為「清空 client marked text」與「把 `preeditText` 交給候選面板」兩個獨立步驟。
- 候選面板的顯示條件從只有 `_candidateCount > 0` 擴大為「有候選或有待確認文字」。
- 取得候選框位置時，改以 client 真正的目前插入點為主，不再假設 client 內含 `preeditText` 長度，避免外掛組字後游標定位偏移。

### `ZYCandidatePanel` / `ZYCandidateView`

- 增加 `preeditText` 顯示屬性與更新 API；一般候選、Emoji／標點模式皆可傳入空白或非空 header。
- 頂端保留一列組字 header，候選網格的起始 Y 座標與面板高度據此下移；沒有待確認文字時維持目前候選布局，不額外增加空白。
- 只有待確認文字、沒有可選候選時，建立一列不可點選的最小面板；既有繁／簡、說明與清除學習按鈕位置維持可用且不遮擋 header。
- `orderOut:` 必須清除 header，避免切換 App 或下一次輸入殘留前一段組字。

## 例外與相容性

- `Esc`、Shift 取消未確認注音、切英文與 input controller 關閉時，均要清除 client marked text、候選 header 與內部狀態。
- Emoji／標點特殊模式僅在有一般待確認組字時顯示 header；獨立開啟特殊候選時不顯示空白 header。
- 說明與清除學習卡片依候選框新高度重新定位。

## 測試

1. 新增靜態回歸測試：未完成組字不得再呼叫 `setMarkedText:preeditText`；非空 pending state 必須傳進候選面板。
2. 新增候選面板靜態測試：header 會繪製、候選網格會在 header 下方開始、空候選但有 preedit 時仍保留面板。
3. 執行現有 Core、候選面板、組字控制器與完整測試套件。
4. 手動測試 `http://127.0.0.1:8080/`：輸入 `ㄋㄧㄏㄠˇ` 後按 Enter 選字，不得送出注音；再按 Enter 才送出已確認的「你好」。

## 成功標準

- 注音不再出現在一般 App 的游標旁，而在候選框上方可辨識地呈現。
- 已選但未送出的中文仍對使用者可見。
- 本機 AI 聊天網頁第一次 Enter 不再送出 `ㄋㄧㄏㄠˇ`；最終確認後的 Enter 仍可送出中文。
- 既有候選選擇、學習、繁簡輸出與面板控制不回歸。
