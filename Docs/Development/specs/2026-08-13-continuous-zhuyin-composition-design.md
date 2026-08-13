# 連續注音自動分詞／組句設計

## 目標

讓使用者不必在每個詞後按 Enter。輸入一整串連續注音時，輸入法能把它切成多個詞並顯示完整組句候選。

主要回歸案例：

- `ㄐㄧㄣㄊㄧㄢ` → `今天`
- `ㄊㄧㄢㄑㄧˋ` → `天氣`
- `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` → `今天天氣`
- `ㄐㄧㄣㄊㄧㄢㄊ` → 可以保留 `今天`，尾端以未完成音節繼續預測
- 不自動提交前詞；整串仍是 marked text，最後由使用者一次 Enter 確認。

## 架構

### 1. ZYEngine：前綴詞匹配

新增 `zy_engine_lookup_prefix()`。它不要求候選詞吃完整個 query，而是回傳「從 query 開頭可以吃掉多少個注音 codepoint」的候選。

每個候選增加：

- `consume_codepoints`：此候選消耗的 query codepoint 數。
- `word_complete`：候選詞本身的所有音節是否已完整匹配。

規則：

- 完整詞可以只吃 query 的前綴，例如 query 為 `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` 時，`今天` 是完整詞並只消耗前半。
- 最後一個音節尚未輸入完成時，仍可作為 terminal partial 候選；partial 不可作為中間切段。
- 保留既有完整音節、無聲調音節、聲母縮寫與 trailing partial syllable 規則。

### 2. ZYComposer：Beam Search 組句

新增純 C `Core/ZYComposer.c/.h`。

限制：

- 最多 8 個詞段。
- 最多 32 個音節級匹配範圍；實際以 query UTF-8 codepoint offset 建圖。
- Beam width 32。
- 每個位置最多展開前 12 個 prefix 候選。

搜尋狀態包含：

- query codepoint offset
- segment count
- cumulative score
- segment candidate IDs
- 每段 consume_codepoints
- 合併後文字

只有完整詞可繼續展開；未完成尾音節只能作為最後一段。

### 3. 組句排序

避免「切越碎分數越高」，不直接累加候選原始固定 class 分。

每段 lexical score 由：

- 字典權重
- 完整詞獎勵
- 多音節詞獎勵
- partial 尾段折扣

組句額外：

- 每多一段扣 segment penalty，偏好較少、較長的合理詞段。
- 完整吃完 query 的路徑優先於 literal fallback。

實際常數由測試鎖定，首要條件是 `今天 + 天氣` 必須高於拆成單字的路徑。

### 4. ZYRuntime：學習加權

`ZYRuntimeLookup()`：

1. 取得原本單一詞候選。
2. 取得組句候選。
3. 對單一詞套既有 query preferred、recency、frequency。
4. 對組句中的每一段套 constituent learning bonus；組句本身若已存在 user phrase，再給 phrase learning bonus。
5. 合併、排序、去重後回傳前 40。

不更改 v0.1.12 起的學習上限／近期性資料格式。

### 5. ZYInputController：選中組句後拆成 pieces

`ZYCandidate` 擴充固定大小的 segment metadata：

- `segment_count`
- `segment_ids[8]`
- `segment_consume_codepoints[8]`

選擇普通單詞時維持原流程。

選擇組句時，controller 依 segment metadata 把它拆成多個 `ZYPendingPiece`，每一段保存：

- word
- 對應 query slice
- pronunciation key

最後 Enter 時沿用目前 `learnAndCommit:`：

- 各 constituent word 正常學習。
- 連續 word run 會額外學成 phrase，例如 `今天天氣`。
- 只在最終 Enter 時學習；僅瀏覽候選不學習。

## 錯誤與退化策略

- 若組句搜尋沒有完整路徑，保留原本單詞／單字候選，不阻塞輸入。
- 若組句 metadata 超過 8 段，不產生該路徑。
- 若合併文字超過 `ZY_CANDIDATE_WORD_BYTES`，捨棄該路徑。
- literal 候選仍保持最低順位。

## 測試

必須新增：

1. prefix lookup：`今天` 可以從 `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` 吃掉正確前綴。
2. composer：整串 `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` 第一候選為 `今天天氣`。
3. partial tail：`ㄐㄧㄣㄊㄧㄢㄊ` 可產生以 `今天` 開頭的組句預測。
4. no auto commit：Controller 的連續注音仍留在 marked composition，未按 Enter 不寫學習。
5. selection expansion：組句候選可拆成兩個 word pieces，最後 Enter 同時學 constituent 與 phrase。
6. 既有 `記憶體` partial syllable、adaptive learning、OpenCC、Emoji/標點、F9、候選窗定位全部回歸通過。
