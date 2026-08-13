# Learned Final-Syllable Partial Recall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recall a previously confirmed multi-syllable dictionary word when the query has reached all of its syllables but the final syllable is still being typed, without promoting the word too early.

**Architecture:** The engine exposes a non-persistent `final_syllable_partial` candidate flag when matching consumed the whole query, reached every dictionary syllable, and stopped inside the final syllable. Runtime reuses the existing learned-word soft preference rank for either a dictionary-exact match or this narrow final-partial state. Learning file formats and scoring remain unchanged.

**Tech Stack:** C99 core engine, Objective-C++ runtime, Python static regression tests.

## Global Constraints

- Keep all v0.1.20 behavior and features.
- Do not change the persistent learning snapshot format.
- `ㄗㄌ` must not soft-promote `資料庫` merely because it is learned.
- `ㄗㄌㄎ`, `ㄗㄌㄎㄨ`, and `ㄗㄌㄎㄨˋ` may recall learned `資料庫` once the query has reached its third syllable.
- Exact same-query preference rank 2 remains stronger than learned-word soft rank 1.

---

### Task 1: Expose final-syllable-partial match metadata

**Files:**
- Modify: `Core/ZYEngine.h`
- Modify: `Core/ZYEngine.c`
- Test: `Tests/test_engine.c`

**Interfaces:**
- Produces: `ZYCandidate.final_syllable_partial` (`uint8_t`).

- [x] Write a failing engine test for `ㄗㄌㄎ -> 資料庫` metadata and `ㄗㄌ` negative boundary.
- [x] Verify the test fails before production changes.
- [x] Populate `final_syllable_partial` only when the match reached all dictionary syllables but the final syllable is incomplete.
- [x] Run native core tests.

### Task 2: Reuse learned-word soft recall for the narrow partial state

**Files:**
- Modify: `App/ZYRuntime.mm`
- Modify: `Tests/test_learned_abbreviation_recall_static.py`

**Interfaces:**
- Consumes: `ZYCandidate.final_syllable_partial`.
- Produces: `preference_rank=1` for previously learned multi-syllable exact or final-syllable-partial matches.

- [x] Add a failing static regression for the runtime condition.
- [x] Extend the soft recall condition without changing rank 2 behavior.
- [x] Run the full regression suite.

### Task 3: Release verification

**Files:**
- Modify: `App/Info.plist`
- Modify: `README.md`

- [ ] Bump to v0.1.21 / build 22 and document the partial learned-word recall rule.
- [ ] Run the complete suite from the working tree.
- [ ] Package the ZIP, extract it to a fresh directory, and run the complete suite again.
- [ ] Verify executable permissions and installer shell syntax.
