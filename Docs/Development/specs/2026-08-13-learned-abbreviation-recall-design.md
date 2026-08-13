# Learned Abbreviation Recall Design

## Goal

Ensure previously learned multi-syllable words can be recalled from abbreviated Bopomofo queries even when their raw dictionary rank is outside the normal display window, while preventing the composer from being dominated by single-character fallback edges.

## Behavior

- Query `ㄗㄌㄎㄨˋ` must be able to recall `資料庫` from the dictionary even if its unlearned raw rank is beyond the first 40 candidates.
- Personal learning is applied after a wider dictionary recall stage and before final truncation to the visible candidate count. A previously selected multi-syllable word that exactly matches all query syllables (including mixed initial abbreviations) receives soft preference rank 1; exact same-query recent choice remains rank 2.
- Composer prefix expansion reserves a small capacity for candidates matching at least 3 syllables so single-character fallbacks cannot consume all edge slots, while avoiding noisy two-syllable abbreviation ambiguity.
- Learned words and long dictionary words remain eligible; no word-specific special cases are added.
- Existing continuous composition, explicit first tone, quality filtering, quick help, Traditional/Simplified output, Emoji/punctuation, and adaptive learning behavior remain unchanged.

## Architecture

`ZYRuntimeLookup` asks the engine for a wider recall pool (128 candidates), applies query/word learning, merges composition and learned phrases, then performs final ranking and deduplication into the caller's requested capacity. `zy_engine_lookup_prefix` still performs dictionary matching, but its output selection is diversified so multi-syllable candidates retain slots even when many one-character fallbacks have higher raw phonetic scores.

## Memory

The wider runtime recall pool is stack allocated and remains small (well under 100 KB). No new resident model or large table is added.

## Tests

- Engine regression: `資料庫` is present within a 128-candidate lookup for `ㄗㄌㄎㄨˋ` while documenting that it can fall outside 40.
- Composer regression: `資料庫` remains reachable as a multi-syllable prefix edge for `ㄗㄌㄎㄨˋ` and low-quality single-character combinations do not crowd all edge slots.
- Runtime static regression: wider recall happens before learning and final truncation.
