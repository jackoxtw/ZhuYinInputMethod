# 版本歷程

## v0.1.72 / build 75

- Return Guard 改為三層路由，優先 `CGEventTapCreateForPid(frontmostPID, ...)`，直接過濾準備送往目前瀏覽器／App 的 Return；失敗才退回 `kCGAnnotatedSessionEventTap`，最後才使用原本的 `kCGSessionEventTap`。
- InputMethodKit controller 在組字狀態同步時發布 `NSWorkspace.frontmostApplication.processIdentifier`；只有目標 PID 改變才重建 tap，避免 per-keystroke churn。
- per-PID tap 吞掉實體 Enter 後，仍由 main queue 呼叫原本 `consumeReturnWhileComposing:`，因此候選選取、快速確認、學習與 commit 規則不另寫第二套。
- 設定頁新增目前 tap 路徑與 PID；保留 Tap／Enter／armed／drop 計數，可同時判斷「tap 根本沒看到事件」與「事件看到了但未 armed」。
- 保留 build 74 的專用 CFRunLoop thread、常駐 active filter、atomic 共享狀態、Mach port 失效自癒、Return/Keypad Enter keyDown+keyUp 配對攔截與 repeat 防連發。
- 標準 InputMethodKit `keyCode=229 / isComposing` 路徑仍保留，未授權 Accessibility 時不影響既有輸入。

## v0.1.70 / build 73

- 修正 build 72「輔助使用看似已授權，但 CGEventTap 未真正攔住 Enter」：輸入法程序改為 accessory agent（`LSBackgroundOnly=false`、`LSUIElement=true`）。
- Return Guard 新增實際 Event Tap 建立／啟用狀態與 keyDown/keyUp 攔截計數。
- 設定頁可重新檢查／啟動 Guard，不再把 `AXIsProcessTrusted()` 等同於 Guard 已工作。
- 保留 IMK `229 + composing` 第一層防護與 Emoji／標點 marked composition。

## v0.1.69 / build 72

- 網頁聊天 Enter 防誤送升級為兩層架構：保留 InputMethodKit `handleEvent:client:` 正規 consume 路徑，新增可選的系統級 Return Guard。
- 新增 `ZYReturnGuard.mm`：使用 `kCGSessionEventTap + kCGHeadInsertEventTap + kCGEventTapOptionDefault`，只在逐音有組字／候選時啟用，直接刪除 Return（36）與 Keypad Enter（76）的實體 keyDown/keyUp，因此取得權限後網頁 JavaScript 不會收到確認候選用的 Enter。
- Return Guard 只監看 Enter/Keypad Enter；閒置時 event tap 關閉，正常 Enter 完全放行。長按 repeat 不會連續推進候選階段，並保留配對 keyUp 攔截直到實體按鍵放開。
- 設定頁新增「完整防誤送」與「授權輔助使用」。未取得 Accessibility 權限時不會在打字途中自動跳權限提示，而是透明退回既有 InputMethodKit 安全模式。
- 修正 Emoji／中文標點候選模式先前未同步 `markedText` 的缺口；開啟／關閉特殊候選時現在也同步 composition 狀態，避免瀏覽器把特殊候選的 Enter 當成一般送出鍵。
- 新增 `test_strict_return_guard_static.py`，固定檢查 active event filter、Return/keyUp 雙向攔截、repeat 防連發、權限只由設定頁主動請求、特殊候選 marked state 與正式 build script 連結。

## v0.1.68 / build 71

- 補齊台灣交通與道路詞庫：新增 17,565 個道路主名稱，建置時會移除「一段／二段…」等段別，避免同一路名因段數重複膨脹。
- 新增 543 筆台灣軌道車站來源列，涵蓋台鐵、高鐵、阿里山林鐵、台北／桃園／台中／高雄捷運與輕軌、新北捷運與三鶯線；依系統產生「站／車站／台鐵／高鐵／捷運／機捷／輕軌」等常用輸入別名。
- 新增民航局機場分布頁列出的 17 座機場，並補入桃園機場、桃機、松山機場、小港機場、清泉崗機場、馬公機場等常用別稱。
- 地名產生器擴充道路／車站／機場輸入與完整性檢查；道路、車站、機場來源 CSV 只在建置階段使用，正式執行仍只 mmap 單一 `dictionary.bin`，不增加 CSV 常駐記憶體。
- Bundled ZYDICT2 更新為 98,054 詞；本次地名／交通生成層共 21,529 個 word+pron 項目。Composer workspace 仍維持 build 70 的約 264 KB 上限設計。
- HTML Canvas 原型的內嵌詞庫同步到同一份 build 71 ZYDICT2，新增同步工具並以 byte-for-byte round-trip 測試防止 HTML／原生詞庫再次漂移。
- 新增道路、軌道車站、機場、罕見道路用字、多音字 `期 → ㄑㄧˊ` 與正式查詢引擎回歸測試。

## v0.1.67 / build 70

- 候選 Top-K 熱路徑改為「slot index 排序＋64-bit word hash」：不再為每個匹配候選搬動整個 `ZYCandidate` 結構；低排名同分候選仍保留既有穩定選取語意。
- 候選文字改為 Lazy copy：先以 dictionary mmap 內的字串做 hash／長度判定，只有真正進入 Top-K 的候選才複製到輸出 buffer，減少大量短查詢時的 memcpy。
- `zy_dict_bucket()` 對目前標準注音 bucket 改為固定 index O(1) 查表；非標準／舊字典仍保留 binary-search fallback。
- Composer beam path 移除每條路徑固定 `text[128]`，改存 64-bit output hash、byte length 與 segment IDs；只有最終候選或 hash collision 驗證時才重建文字。
- Composer path 由 184 bytes 降至 64 bytes；129×32 beam workspace（含 counts）由約 760,584 bytes 降至 264,321 bytes，減少約 496 KB（約 65%）。
- 新增 `zy_composer_workspace_bytes()` 與 `test_lookup_optimization.c`，固定檢查 workspace 不超過 300 KB，並驗證常用注音 bucket 的固定查表可正常定位。
- 以 build 69 相同候選資料做結果比對，完整／prefix／composer 的代表性查詢輸出保持一致。
- 微基準（同一測試環境）中，`ㄐ` 完整查詢約由 2.18 ms 降至約 0.77 ms；不同查詢依 bucket 大小約有 1.3～2.8 倍不等改善。

## v0.1.66 / build 69

- 新增台灣完整行政區地名層：22 縣市、368 鄉鎮市區全部納入正式 `dictionary.bin`。
- 行政區同時加入完整名稱、常用去尾碼名稱與「縣市＋鄉鎮市區」組合；含 `臺/台` 常用異體，例如「臺北市／台北市」、「臺東／台東」。
- 新增 207 個常用國家／地區名稱與常見別稱，包括臺灣、日本、韓國、美國、加拿大、英國、法國、德國、冰島、烏克蘭、澳洲、紐西蘭等。
- 新增地名專用讀音覆寫，修正「三重、埔里、朴子、茄萣、三地門、元長、長治、長濱」等一般單字讀音無法直接套用的地名。
- 新增 `taiwan_admin_divisions.csv`、`common_country_region_names.csv` 與 `build_geographic_words.py`；安裝時即使重新套用 libchewing-data，也會重新生成並注入地名層，不會遺失。
- Bundled ZYDICT2 由 76,724 詞增加至 78,427 詞；地名生成層共 1,871 個 word+pron 項目，其中 1,703 筆為新詞、168 筆更新既有同讀音權重。
- 新增資料完整性與引擎回歸測試：固定檢查 22／368 數量、所有生成地名都存在於 bundled dictionary，並驗證三重、埔里、苗栗縣南庄鄉、美國、冰島等可由正式查詢引擎召回。

## v0.1.65 / build 68

- 學習儲存升級為 `ZYLEARN3`；保留 `ZYLEARN1` / `ZYLEARN2` 無痛讀取與自動遷移。
- 跨程序保存不再以完整 snapshot 的 `max(count)` 合併，改為在 file lock 內讀取最新 generation，再重播本程序尚未落盤的 word/query/phrase delta；兩個程序同時對同一詞各 +1 時不再遺失一次學習。
- 個別刪除改以 pending delete 狀態參與下一次 merge；舊程序之後只保存其他詞時，不會把已刪除的學習資料復活。整體「清除學習」仍由 `reset_serial` 保證較新的 reset 優先。
- 使用者 phrase 由固定 `query[256] + pron[512]` 改為單一 `key[512] + key_kind`，容量仍維持 1024；加上並行 delta metadata 後，`ZYLearning` 結構由 1,290,288 bytes 降至 1,094,720 bytes，約降低 15.2%。
- 主詞庫升級為 `ZYDICT2`；載入階段新增 word/pron/syllable/bucket offset sentinel、單調性、syllable ID 與 bucket word ID 範圍驗證，損壞檔在 `zy_dict_open()` 即拒絕。讀取端仍相容 `ZYDICT1`。
- `build_native_dictionary.py`、台灣讀音修補與品牌詞注入工具同步輸出 / 接受 ZYDICT2。
- Shared Core 新增 Windows 檔案後端：Dictionary / Conversion 在 Windows 使用 binary heap backing，Learning 使用 `_read/_write`、`LockFileEx` 與 `MoveFileEx`；macOS / POSIX 仍維持 mmap、fcntl lock、fsync 路徑。
- 新增同詞併發 +1、刪除防復活、真實 v2→v3 migration、ZYDICT2 損壞索引拒絕與跨平台靜態回歸測試。

## v0.1.64 / build 67

- 將候選學習儲存升級為 Learning v2：字詞 4096、query×candidate 8192、使用者組句 1024，避免舊版 256/128/128 容量過小造成常用記憶被快速淘汰。
- query 學習改為每個「注音查詢 × 候選」各自保留歷史，不再因同一讀音改選另一個字就覆蓋前一個候選的使用次數。
- 字詞與 query 次數改為 32-bit lifetime count；學習字串改用 UTF-8 安全截斷。
- 新增 stable word identity（字詞＋讀音 64-bit key）與 dictionary fingerprint；詞庫重建後可重新綁定現行 word ID，不再永久依賴 dictionary.bin 的數字 ID；若重映射暫時無法配置記憶體，不會提前接受新 fingerprint，下一次啟動仍可重試。
- `ZYLEARN1` 舊快照可自動讀入並升級為 `ZYLEARN2`，保留舊版既有學習資料；legacy 固定長度字串採 bounded UTF-8 migration，避免異常舊檔造成越界讀取。
- A/B snapshot 新增跨程序 file lock、載入最新 generation 後 merge、temp file + fsync + atomic rename，避免新舊輸入法程序同時存在時互相覆蓋學習；v1 ID-only 與 v2 stable-key 同字資料也會合併，不會在遷移競態中產生重複紀錄。
- 最終確認後採 1 秒 debounce 落盤；持續輸入達門檻仍會立即保存。controller 關閉、切換 App / deactivate 與 Runtime shutdown 皆改為強制 flush；生命週期切換只提交已經選好的 staged pieces，不會因切 App 自動替未完成注音選字。
- 清除學習改為鎖定後寫入兩份空白新 generation，避免舊程序或備援 snapshot 把已清除的學習重新帶回來。
- 開發安裝與 Release 安裝器會先以 Cocoa quit 正常結束舊輸入法，讓 `applicationWillTerminate` 有機會保存學習；僅程序真的卡住時才使用強制結束。
- 新增 Learning v2 容量、多候選、>255 次數、UTF-8、並行 merge、v1 migration 與 Runtime flush 回歸測試。

## v0.1.63 / build 66

### Enter 確認模式

- 設定頁新增「輸入行為 → Enter 確認模式」，提供「瀏覽器安全模式」與「快速確認模式」。
- 預設維持瀏覽器安全模式：選完最後候選後，下一次 Enter 才提交完整中文，避免聊天網站把候選確認鍵誤當送出。
- 快速確認模式：最後一段候選選定的同一次 Enter 立即提交完整中文，但該次 Enter 仍由 InputMethodKit 消耗，不會傳給網頁作為聊天送出。
- 模式以 `NSUserDefaults` 儲存，重新啟動輸入法後保留設定；未設定過的既有使用者仍預設安全模式。
- 保留 v0.1.62 設定頁、v0.1.61 游標定位、右側注音欄與既有學習／候選行為。

## v0.1.62 / build 65

### 候選窗新增設定入口

- 維持 v0.1.61 的 Enter、右側注音欄與游標定位行為不變。
- 候選窗右側原本直接顯示的「清除學習」改為「設定」按鈕，降低誤觸破壞性操作的風險。
- 新增不搶焦點的「逐音輸入法設定」頁面；第一版提供「學習資料」區塊與「清除學習資料」按鈕。
- 清除學習仍沿用既有的二次確認、成功／失敗結果與 `ZYRuntimeClearLearning()` 路徑，不變更學習資料格式。
- `Esc` 可先關閉設定頁；候選窗隱藏或輸入 session 結束時也會釋放設定頁資源。

## v0.1.61 / build 64

### 螢幕底部候選窗定位修正

- 修正 `IMKTextInput attributesForCharacterIndex:lineHeightRectangle:` 的 index 使用方式：改用 inline composition 相對索引；沒有 inline session 時固定以 `0` 取得目前選取位置，不再誤用文件絕對 `markedRange`／`selectedRange`。
- 移除 caret 取得失敗時把候選視窗定位到 `visibleFrame` 正中央的假游標 fallback，避免網頁輸入框位於螢幕底部時候選窗跳到螢幕中央。
- caret 短暫不可用時只沿用最後一次已驗證的真實 caret；首次查詢仍不可用時不移動候選窗，等待後續有效位置。
- 保留 v0.1.60 的四向翻面、v0.1.59 右側注音欄與 v0.1.58 Enter 狀態機。

## v0.1.60 / build 63

### 候選視窗游標貼附修正

- 候選視窗定位改為四向翻面：預設游標右下，右側不足時先翻到游標左側，下方不足時先翻到游標上方。
- 候選框只有在左右或上下都無法完整容納時才退回螢幕可視範圍裁切，避免寬候選框被直接釘在螢幕邊緣而遠離文字游標。
- 保留 6 pt 游標間距、v0.1.59 右側注音欄，以及 v0.1.58 已確認正常的 Enter 狀態機。


本文件記錄逐音輸入法的版本更新。最新版本請見 [README](README.md)。

## v0.1.59 / build 62

### 未完成注音移至候選窗最右側

- 候選窗上方的待確認列改為左右分區：左側保留已選待確認內容，最右側使用固定欄位顯示尚未完成的注音。
- 未完成注音在右側欄位內明確靠左對齊，不再與已選內容串接在同一段文字中。
- 保留 v0.1.58 已確認正常的 Return／Enter 狀態機，不更動選候選、提交與網頁送出流程。

## v0.1.58 / build 61

### Return 第二次按下無反應修正

- 修正 v0.1.57 將 HTML 的 `keyup` 鎖直接移植到 InputMethodKit 後，Return／Enter 可能因 macOS 未回送對應 KeyUp 而永久維持 `_handledKeyDown`，造成第一次選候選後後續 Enter 全部無反應。
- Return／Enter 不再使用持久 `_handledKeyDown` 鎖；只使用 `NSEvent.isARepeat` 攔截長按自動重複。
- 其他需要 keyDown／keyUp 配對的已處理按鍵仍保留原本 latch，不影響既有快捷鍵。
- 操作順序維持：第一次 Enter 選目前候選；下一次新的 Enter 提交已確認文字；組字完全結束後再下一次 Enter 才交給應用程式。

## v0.1.57 / build 60

- 修正 `ZYCandidatePanel.mm` 編譯錯誤：`preeditHeaderHeight` 僅保留於 `ZYCandidateView`，不再誤用於 `ZYHelpView` / `ZYClearLearningView`。

### 同步 HTML 逐段 Enter 狀態機

- 正式版完整同步已驗證可用的 HTML Enter 行為：有候選時每一次實體 Return／Enter 只確認目前反白的一個候選。
- 新增 Return／Enter 實體按鍵鎖；同一顆按鍵尚未 KeyUp 前產生的 repeat KeyDown 全部攔截，不能在一次長按中連續「選候選 → 提交 → 送出」。
- 已選候選與未完成注音都不再作為可見 marked text 放在應用程式游標旁；客體只收到不可見 IME placeholder。
- 候選窗上方改為顯示「已選內容／未完成注音」，完整呈現 staged pieces + 尚未完成的注音。
- 全部候選選完後，候選窗仍保留待確認內容；下一次 Enter 才提交中文，再下一次 Enter 才會放行給網頁聊天室。
- 中文標點邊界也改為最多只選一次目前候選，不再自動一路解析剩餘候選。
- 專案內 HTML Reference 同步為本次已驗證的逐段 Enter 版本。

## v0.1.55 / build 58

### Enter 只確認目前候選

- 修正候選字仍存在時按 Return／Enter 會自動把剩餘注音候選全部解析並直接提交整段文字的問題。
- Return／Enter 在候選窗可見時現在只確認目前反白的一個候選，立即結束該次按鍵處理，不會同時執行整段提交。
- 已選候選會先保留在逐音的 staged composition；只有候選與未完成注音都已清空後，再按一次 Return／Enter 才提交已確認文字。
- 未完成注音仍只顯示在候選窗上方，不會回到文字游標旁。

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
