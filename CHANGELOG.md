# 版本歷程

本文件記錄逐音輸入法的版本更新。最新版本請見 [README](README.md)。

## v0.1.55 / build 58

### 浮動注音組字列編譯修正

- 修正 `ZYCandidatePanel.mm` 將 `preeditHeaderHeight` 誤加入 `ZYHelpView` 與 `ZYClearLearningView`，造成兩個類別引用不存在的 `preeditText` 屬性而無法編譯。
- `preeditText` 與 `preeditHeaderHeight` 現在只由真正的 `ZYCandidateView` 持有與使用。
- 新增類別邊界回歸檢查，避免候選組字列專用方法再次被誤插到說明／清除學習 View。

## v0.1.54 / build 57

### 浮動注音組字列／網頁聊天防誤送

- 未完成的注音讀音不再放進應用程式的可見 marked text；例如 `ㄋㄧㄏㄠㄚˉ` 只顯示在逐音候選窗上方的「注音」列。
- 文字游標端只保留不可見的 IME placeholder，讓 InputMethodKit／Chromium 繼續知道輸入法正在組字，但網頁 DOM 不再持有可見注音符號。
- 候選窗即使暫時沒有字詞候選，只要仍有未完成注音就會保持顯示，避免使用者看不到目前讀音。
- Return／Enter 只會解析候選並提交確認後的中文；無法解析的殘缺注音不再 fallback 成普通注音文字送進網頁。
- 系統因切換焦點等原因要求強制結束組字時，無法解析的殘缺注音會被丟棄，不會以注音符號插入目標欄位。
- 候選窗定位改以客體的 marked/selected range 取得游標位置，不再以隱藏注音字串長度估算 character index。

## v0.1.53 / build 56

- 修正網頁聊天中，組字期間按 Return/Enter 仍會觸發送出的問題。
- 組字文字改為直接同步寫入 IMKTextInput `setMarkedText:`，不再依賴 `updateComposition` 間接更新。
- 新增 KeyUp 事件接收；輸入法已處理的 KeyDown 會連同對應 KeyUp 一起攔截。
- Return/Enter 改為同步確認組字，並在事件處理前再次發布 marked text。

## v0.1.52 / build 55

### 網頁聊天室 Return 防漏事件修正

- 修正 v0.1.51 僅調整 composition lifecycle 仍不足以阻止部分 Chromium／WebKit 聊天欄收到同一次 `Enter` 的問題。
- 在組字、候選、已確認片段或 Emoji／標點候選仍存在時，Return 當下會同步重新發布非空 marked text，讓瀏覽器把該鍵維持在 IME composing／ProcessKey 路徑。
- 真正的候選解析與 `insertText:` 提交延後到目前 native keydown 完整結束後執行，避免 composition 在瀏覽器建立 DOM 鍵盤事件前被提前清除。
- 主鍵盤 Return（key code 36）與數字鍵盤 Enter（key code 76）統一走同一條安全提交路徑。
- 行為調整為：第一次 Enter 完成並提交目前中文組字，但不交給聊天室；組字已完全清空後，下一次 Enter 才正常交給網頁送出。

## v0.1.51 / build 54

### 網頁聊天 Enter／IME 組字修正

- macOS 正式版改用 `IMKInputController` 的 `composedString:` + `updateComposition` 維持系統組字生命週期，不再由 `updateMarked:` 直接呼叫 client 的 `setMarkedText:`。
- 候選字仍在組字期間時，第一次 `Enter` 只確認目前候選並維持 marked composition；完成組字後再次 `Enter` 才交由網頁聊天室作一般送出。
- 新增 `commitComposition:`，處理瀏覽器／應用程式主動要求結束組字時的候選解析、提交與清理，並在提交後明確發布空 composition，避免下一個 Enter 與前一個 IME session 混在一起。
- 保留 `updateMarked:` 的局部 `@autoreleasepool` 記憶體最佳化。

## v0.1.50 / build 53

### Gatekeeper 安裝指引

- 一般使用者說明與 Release 內附說明新增直接雙擊 `.command` 被 macOS 阻擋時的完整處理流程：按「完成」後到「系統設定 → 隱私權與安全性」，按「強制打開」並確認「打開」。

## v0.1.49 / build 52

### 等長候選 + 學習延伸詞

- 目前輸入匹配幾個注音音節，候選前段就優先顯示相同字數的完整詞：1 音節優先 1 字、2 音節優先 2 字、3 音節優先 3 字，以此類推。
- 等長候選後方只接上「曾經真正學習過、且讀音可由目前輸入繼續延伸」的較長詞；一般未學習的長詞不再佔據前段候選。
- 有學習延伸詞時，前段等長候選最多保留 20 個位置，讓學習詞不會被大量單字／短詞淹沒。
- 學習延伸詞先依字數由短到長排列，同長度再依個人使用頻率、最近使用與既有候選排名排序。
- 修正同一可見詞同時存在於內建詞庫與自訂學習詞時，去重流程可能丟失學習狀態的問題；現在會保留可刪除的學習候選身分。
- HTML 試用版與 macOS 原生正式版同步上述候選策略；Emoji、`'` 中文標點、F9、第一聲 Space 與既有學習資料格式不變。

### 說明面板

- 候選面板右側的「繁／簡」與「說明」按鈕改為貼齊頂端，讓候選面板高度改變時位置一致。
- 快速使用說明新增可點擊的 GitHub 專案連結，可直接開啟專案首頁。

## v0.1.48 / build 51

### 英文切換保護

- 單按 `Shift` 切換至英文時，尚未用 Enter、Space、數字或滑鼠確認的注音會直接取消，不會誤送出候選中文。
- 已確認的中文片段會先送出，再切換英文；`Shift + 英文字母` 也採相同的已確認／未確認處理順序。
- macOS 原生版與 HTML 試用版同步此行為，並補足候選快捷鍵、Caps Lock 與 HTML／原生一致性回歸測試。

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
