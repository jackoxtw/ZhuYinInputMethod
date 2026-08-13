# Learned Abbreviation Recall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Recall learned multi-syllable words from abbreviated Bopomofo queries even when raw dictionary rank exceeds the display window, without allowing single-character composer fallbacks to crowd out real words.

**Architecture:** Widen the runtime dictionary recall pool before applying adaptive learning, then truncate only after all ranking signals are merged. Diversify composer prefix edges so 3+ syllable candidates retain capacity alongside single-character fallbacks, and assign a soft learned-recall preference to previously selected exact multi-syllable matches.

**Tech Stack:** C99 core engine/composer, Objective-C++ AppKit runtime, Python static regression tests, shell test runner.

## Global Constraints

- Preserve all v0.1.19 behavior and data formats.
- No word-specific special cases for `資料庫`.
- No large resident language model or new persistent database.
- Keep visible candidate capacity controlled by the caller.

---

### Task 1: Wider learned recall

**Files:**
- Modify: `App/ZYRuntime.mm`
- Test: `Tests/test_learned_abbreviation_recall_static.py`

**Interfaces:**
- Consumes: `zy_engine_lookup`, existing adaptive learning functions.
- Produces: wider pre-learning recall pool with final caller-cap truncation unchanged.

- [x] Add a failing static regression proving runtime still asks for only 40 raw candidates.
- [x] Run the regression and confirm failure.
- [x] Change raw dictionary recall to 128 while retaining the existing 192 merge buffer.
- [x] Run regression and existing runtime tests.

### Task 2: Prefix edge diversity

**Files:**
- Modify: `Core/ZYEngine.c`
- Test: `Tests/test_engine.c`
- Test: `Tests/test_composer.c`

**Interfaces:**
- Consumes: dictionary prefix matching and `ZYCandidate` metadata.
- Produces: prefix lookup where multi-syllable word candidates cannot be entirely displaced by one-character fallbacks.

- [x] Add a failing regression for `ㄗㄌㄎㄨˋ` showing `資料庫` must remain reachable in prefix results.
- [x] Run the regression and confirm failure.
- [x] Implement bounded edge diversity with no per-word special case.
- [x] Run engine and composer tests.

### Task 3: Release verification

**Files:**
- Modify: `README.md`
- Modify: `App/Info.plist`
- Modify: `run_core_tests.sh`

**Interfaces:**
- Produces: v0.1.20 / build 21 release artifact and documented learned abbreviation recall.

- [x] Add new regression to full test runner.
- [x] Update README and version metadata.
- [x] Run full regression suite.
- [x] Package ZIP, extract to a clean directory, rerun full suite, and verify executable script permissions.
