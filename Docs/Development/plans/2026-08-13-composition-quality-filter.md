# Continuous Composition Quality Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Keep natural continuous-composition candidates such as「現在有」at the top while removing low-quality phonetic combinations such as「先在有」「線在有」without adding a large language model or meaningful persistent memory usage.

**Architecture:** Keep phonetic path generation in `ZYComposer.c`, but expose a normalized composition quality score and penalize unnecessary segmentation. In `ZYRuntime.mm`, cap constituent learning at the composition level instead of summing unlimited per-segment bonuses, then apply a relative quality gate before mixing composed candidates with dictionary/user-phrase candidates.

**Tech Stack:** C99 core engine/composer, Objective-C++ runtime, Python static regression tests, existing binary Taiwan dictionary.

## Global Constraints
- Preserve dictionary, OpenCC, continuous composition, adaptive learning, Emoji/punctuation, F9, and adaptive candidate layout.
- Do not add a large language-model data file.
- Do not increase persistent learning format or require migration.
- Prefer fewer high-quality composition candidates over filling the page with poor combinations.
- Existing learned preferences must still influence natural candidates, but constituent bonuses must not grow with segment count without a cap.

---

### Task 1: Lock the bad composition case

**Files:**
- Modify: `Tests/test_composer.c`

**Interfaces:**
- Consumes: `zy_composer_lookup()`
- Produces: regression expectations for `ㄒㄧㄢㄗㄞㄧㄡˇ`

- [x] Add assertions that「現在有」is first and that obvious fragmented combinations do not survive the high-quality result window.
- [x] Run the composer test and confirm the current implementation fails the new quality assertion.

### Task 2: Penalize unnecessary segmentation in the composer

**Files:**
- Modify: `Core/ZYComposer.c`
- Test: `Tests/test_composer.c`

**Interfaces:**
- Consumes: dictionary word weight, matched character count, word completeness, segment count
- Produces: composed candidates whose score preserves a meaningful distance between long known words and character-by-character paths

- [x] Prefer longer complete dictionary edges over equivalent single-character fragmentation.
- [x] Increase the per-extra-segment penalty enough to stop `先 + 在 + 有` from clustering near `現在 + 有`, while preserving legitimate sentences that necessarily use single-character words.
- [x] Run `test_composer` and keep existing「今天天氣」and partial-tail tests green.

### Task 3: Normalize runtime learning for compositions

**Files:**
- Modify: `App/ZYRuntime.mm`
- Modify/Create: `Tests/test_composition_runtime_static.py`

**Interfaces:**
- Consumes: per-word frequency, recency, query bonus, preference rank
- Produces: one capped composition learning bonus

- [x] Replace raw sum of every constituent learning signal with bounded buckets: frequency, recency, query, and preference.
- [x] Keep strong exact/recent preferences useful, but cap total composition learning so extra segmentation never provides an automatic advantage.
- [x] Stop compressing composer score with `/20`; use a scale that preserves the composer quality gap without overflowing `int32_t` final candidate scores.
- [x] Add static regression checks for the cap and removal of `/20`.

### Task 4: Relative composition quality gate

**Files:**
- Modify: `App/ZYRuntime.mm`
- Test: `Tests/test_composition_runtime_static.py`

**Interfaces:**
- Consumes: ranked composed candidate scores
- Produces: only high-quality composed candidates appended to the normal candidate pool

- [x] Establish the best composed score for the query.
- [x] Drop composed candidates below a relative score floor and cap the number admitted to runtime.
- [x] Do not force a minimum count: one or three good candidates is valid.
- [x] Verify normal dictionary candidates and user phrases remain available.

### Task 5: Restore v0.1.17 quick-help feature on the working base and release

**Files:**
- Modify: `App/ZYCandidatePanel.h`
- Modify: `App/ZYCandidatePanel.mm`
- Modify: `App/ZYInputController.mm`
- Modify: `README.md`
- Modify: version/build metadata
- Add/restore: quick-help static regression test

**Interfaces:**
- Preserves the approved v0.1.17 UI: help button below 繁/簡, lazy non-activating help panel, toggle/escape close behavior.

- [x] Reapply the approved quick-help behavior because the locally available base artifact is v0.1.16.
- [x] Ensure single-row candidate panels retain enough height for both right-side buttons.
- [x] Run all static panel/controller tests.

### Task 6: Full verification and packaging

**Files:**
- Modify: `run_core_tests.sh` only if a new test must be registered
- Package: `zhu-yin-input-method-native-v0.1.18-composition-quality-filter.zip`

- [x] Run the complete C and Python regression suite.
- [x] Run shell syntax and executable-permission checks.
- [x] Package the project.
- [x] Extract the final ZIP into a clean directory and rerun the full suite.
- [x] Directly print the top results for `ㄒㄧㄢㄗㄞㄧㄡˇ` and verify「現在有」is first and obvious garbage candidates are filtered.
