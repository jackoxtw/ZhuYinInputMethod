# 自適應候選學習排序設計

## 目標
讓逐音輸入法的學習排序同時兼顧「最近常用」與「長期常用」，並避免歷史使用次數無限膨脹造成候選永久霸榜。

## 核心規則

1. **一次 Enter = 一個 learning event**：同一次確認內的所有字與詞共用同一個 `clock` 值。
2. **一般字詞長期頻率封頂**：有效次數 `min(count, 31)`，每次 +4,000，最高 +124,000。
3. **一般字詞近期分數**：最近一次使用最高 +120,000；每經過一個 learning event -4,000；30 次後歸零。
4. **同注音查詢頻率封頂**：有效次數 `min(count, 8)`，每次 +5,000，最高 +40,000。
5. **明確 query preference 有效 64 次**：相同注音最近明確選過的字典候選取得 `preference_rank=2`；超過 64 個 learning events 未再選則失效。
6. **同查詢改選立即替換**：同一 query hash 僅保留最近一次明確選擇。
7. **使用者詞組頻率封頂**：有效次數 `min(count, 16)`，每次 +8,000，最高 +128,000。
8. **使用者詞組近期分數**：最近使用最高 +160,000；每個 learning event -5,000；32 次後歸零。
9. **使用者精確詞組**：精確符合 query 的已學習詞組取得 `preference_rank=1`，低於近期明確選過的字典候選 rank 2，高於普通候選 rank 0。
10. **資料相容**：不改 `ZYLearningPersistent` 結構與 snapshot version。舊 count 可保留至 255，但只在計分時套上限。

## 排序

候選依序比較：
1. literal 永遠最後。
2. `preference_rank`：2 > 1 > 0。
3. `score`：原始詞庫／詞組基礎分 + capped frequency + recency + capped query bonus。
4. 字串穩定排序。

## 學習時機

只有 Enter 最終 commit 才建立 learning event。移動候選游標、開啟候選窗、取消組字都不學習。一次 commit 即使包含多個字、詞組或標點，learning clock 只增加一次。

## 舊資料升級

舊 `learning_A.dat` / `learning_B.dat` 直接載入。若舊 count=173，仍保存 173，但一般字詞有效頻率只按 31 計算。舊 `last` 與 `clock` 保持原值，之後以新的每-commit event clock 繼續前進。
