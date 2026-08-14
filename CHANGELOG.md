# 版本歷程

本文件記錄逐音輸入法的版本更新。最新版本請見 [README](README.md)。

## v0.1.47 / build 50

### 候選操作與 HTML 試用版同步

- 單按 `Shift` 切換英文前會先確認並送出未完成的中文；候選存在時保留 `Shift + 1～0 / A～J` 的快速選字優先順序。
- 按住 `Option` 時，只有已學習候選顯示「刪除」；點選可移除該候選的排序或自訂詞學習資料。
- 已學習單字與多字詞（含縮寫召回）可優先排序；HTML Canvas 試用版同步原生候選面板的深色自適應格局、右側控制列、快速說明與清除學習操作。

## v0.1.46 / build 49

### 候選字型延遲建立

- 已定位完成注音音節時的候選準備會一次建立 12–18pt 全部七種系統字型；現在只建立該頁實際使用的一種字型 attributes，其餘字級首次需要時才建立。
- 避免第一個完整注音音節為未使用的字型大小預先啟動 FontServices／圖形快取；候選外觀、字型、排版與功能不變。

## v0.1.45

### 正常候選單行繪製

- 10 欄短候選與 5 欄中長候選已確定為單行內容，改用 `drawAtPoint:` 直接繪製；不再為每一格在每個按鍵建立多行 `NSStringDrawing` 排版物件。
- 4 欄長組句仍保留原有可換行繪製、12pt 可讀字級下限與格內裁切，避免長詞顯示退化。
- 此變更只針對每鍵候選文字繪製熱路徑；不改詞庫、召回、排序、組句、學習、候選數、面板生命週期或滑鼠選字。

## v0.1.44

### 移除正式版記憶體診斷熱路徑

- 已完成的 `MemoryDiagnosticMode` 分段診斷與測試工具不再隨正式版發行；正常輸入不再每鍵呼叫 `CFPreferencesAppSynchronize`／讀取 `NSUserDefaults`。
- 候選更新現在直接進行 Runtime lookup 與正式候選面板流程，移除診斷用的額外分支和暫存面板路徑。
- 之後需要分析峰值時，改用 Instruments、`vmmap` 與 `heap`，不污染使用者的實際輸入熱路徑。

## v0.1.43

### marked text 瞬間記憶體優化

- `updateMarked:` 現在使用局部 `@autoreleasepool`，讓每鍵建立 preedit text 時的短命 Objective-C 物件在送出 `setMarkedText:` 後立即釋放。
- 不改變 marked text 的內容、游標位置、候選、詞庫、學習或輸入規則。

## v0.1.42

### 候選排版瞬間記憶體優化

- Mode 5 診斷顯示候選文字轉換／排版是主要瞬間配置來源之一；候選準備階段現在完全不再呼叫 `boundingRectWithSize:`。
- 10／5 欄候選以固定單行字型 metrics 計算垂直置中；4 欄長詞只按格寬與字元數一次選擇既有的 12pt 下限，仍維持格內裁切。
- 不改動候選數量、排序、台灣詞庫、連續組句、學習、繁簡轉換、面板生命週期或滑鼠操作。

## v0.1.40–v0.1.41

### 記憶體峰值診斷

- 分段診斷已完成定位任務，並在 v0.1.44 自正式輸入熱路徑移除。
- 不要在 TextEdit 正使用逐音輸入法時強制終止 `ZhuYinInputMethod`；這會硬切斷 InputMethodKit active session，可能造成該登入工作階段暫時只剩英文 pass-through，需重新建立登入 session 才能恢復。

## v0.1.39

### Runtime 每鍵暫存配置優化

- Composer 新增可重用 `ZYComposerWorkspace`；Runtime 初始化時配置一次，之後每次按鍵重用，不再每次組句都配置／釋放 beam 與 count workspace。
- `ZYRuntimeLookup()` 的組句學習 query hash 改為直接對 UTF-8 codepoint 範圍計算，不再為每個 segment 建立 `NSString substringWithRange:`。
- 前 256 個原始候選原本就維持純 C `ZYCandidate` 流程；這版不改候選上限、排序、學習、詞庫或 Composer 品質。
- Runtime shutdown 會釋放 reusable Composer workspace。

## v0.1.38

### caret 查詢瞬間記憶體優化

- 候選定位的 `attributesForCharacterIndex:lineHeightRectangle:` 從逐字回掃改為每次按鍵最多查詢最後一個 inline 字元 1 次，將 caret 查詢由最壞 O(組字長度) 改為固定 O(1)。
- 最後字元若沒有有效座標，立即改走 `firstRectForCharacterRange:`，再依序使用 AX caret 與最近一次有效 caret，不再掃描整段 preedit。
- `clientRect:` 使用局部 `@autoreleasepool`，讓 InputMethodKit／AppKit 定位查詢產生的短命物件在同一次查詢結束時更快釋放。
- 候選數量、詞庫、Composer、學習、Panel 25 MB 級閒置釋放機制與 v0.1.37 grow-only backing-store 行為均不變。

## v0.1.37

### 候選窗 backing-store 峰值優化

- 同一次候選面板顯示期間只允許高度增加，不再因候選欄數／行數變少而反覆縮小，降低 AppKit/WindowServer backing surface 重複配置。
- 候選面板隱藏時立即清空候選字串，但不再先縮回 110pt；若 2 秒內沒有重新使用，沿用既有 idle-release 流程一次性 close/release。
- 下一次新組字若沿用尚未釋放的隱藏面板，顯示前可一次調整到該次實際需要高度，因此不會讓短詞永久沿用上一串的大面板。
- 候選數量、20 個一般候選、Emoji／標點分頁、自適應 10/5/4 欄、滑鼠、學習、詞庫與排序均不變。

## v0.1.36

### macOS 編譯相容性修正

- 修正 v0.1.35 `ZYCandidatePanel` 使用不存在的 `contentSize` getter，造成 Objective-C++ 編譯失敗。
- 候選面板仍只在內容尺寸真正改變時呼叫 `setContentSize:`；目前尺寸改由 `contentView.bounds.size` 取得，因此保留輸入峰值記憶體優化。
- 新增回歸檢查，禁止再次使用 `self.contentSize` getter。

## v0.1.35

### 輸入峰值記憶體優化

- 候選文字尺寸與垂直置中改在候選更新階段預先計算，`drawRect:` 不再反覆執行 `boundingRectWithSize:`。
- 10 欄短候選不做文字矩形測量；長詞候選最多做 1～2 次尺寸測量，最低字級仍維持 12pt。
- 候選面板只有尺寸真的變化時才呼叫 `setContentSize:`，位置真的變化時才呼叫 `setFrame:`。
- 候選窗已顯示時不再每次按鍵重複 `orderFront:`。
- `ZYRuntimeLookup()` 加入局部 `@autoreleasepool`，讓查詢過程的暫存 Objective-C 物件更早釋放。
- 移除已完成定位驗證的 `/tmp/zhu-yin-caret.log` 與 caret trace 程式碼，正式版不再寫入該診斷檔。
- 不縮減台灣詞庫、256 原始候選召回、Composer、學習、OpenCC、Emoji 或標點功能。

## v0.1.34

### 說明面板同步英文大小寫規則

- 快速使用說明新增 `Shift + A–Z`：無候選時 Caps Lock 關閉輸出小寫、開啟輸出大寫。
- `Shift + 1–0 / A–J` 明確標示為「有候選：快速選候選」，避免與英文輸入規則混淆。
- 說明卡高度調整，維持原本間距與底部關閉按鈕。

## v0.1.33

### 空白鍵與 Shift 英文大小寫

- 完全閒置、沒有注音／候選／待確認文字時，`Space` 直接把真正的空格送到目前 App，不經候選或學習暫存。
- 沒有候選時，`Shift + 英文字母` 的大小寫只由 Caps Lock 決定：Caps Lock 關閉輸出小寫，開啟輸出大寫；Shift 本身不再切換大小寫。
- 候選存在時保留原本 `Shift + 1～0 / A～J` 快速選字，不改候選操作。
- 台灣詞庫、學習、Composer、OpenCC、候選排序與記憶體優化行為均不變。

## v0.1.32

### 記憶體與診斷寫入優化

- 移除滑鼠事件診斷 `/tmp/zhu-yin-mouse.log` 與相關檔案寫入。
- 候選面板消失時立即清空候選字串並縮回最小高度。
- 候選面板隱藏 2 秒仍未重新使用時才真正釋放；連續輸入會取消釋放並沿用原面板。
- 候選文字、快捷鍵與右側固定控制標籤共用不可變繪圖 attributes，降低重畫時的短命 AppKit 配置。
- 不縮減台灣詞庫、候選召回、Composer、學習、OpenCC、Emoji 或標點功能。

## 早期記憶體優化

候選 Panel 改為需要顯示時才建立，InputController 停用／關閉時完整釋放；Panel 對 Controller 的 delegate 改回 weak，移除 retain cycle；「說明」與「清除學習」視窗關閉時會連同 content view 與 backing window 一起釋放，下次再 lazy 建立；候選繪圖亦共用常用 paragraph style／attributes，降低重複 AppKit 物件配置。詞庫、學習、連續組句、OpenCC、Emoji、滑鼠與既有介面功能均保留。
