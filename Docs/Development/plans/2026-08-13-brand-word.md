# Built-in Brand Word Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 「逐音輸入法」 as a built-in dictionary brand term that ranks first for its full pronunciation and is recallable from a five-syllable mixed abbreviation without polluting short unrelated input.

**Architecture:** Store brand terms as dictionary data, inject them into the bundled binary dictionary with the existing dictionary serialization helpers, and preserve them through Taiwan reading overlay. Add a generic long-abbreviation soft priority for candidates that have reached at least five syllables, so no brand-specific ranking code is required.

**Tech Stack:** C99 core engine, Objective-C++ runtime, Python dictionary tooling/tests, ZYDICT1 binary dictionary.

## Global Constraints
- Preserve all v0.1.21 functionality.
- Brand word: `逐音輸入法`.
- Pronunciation: `ㄓㄨˊ ㄧㄣ ㄕㄨ ㄖㄨˋ ㄈㄚˇ`.
- Dictionary weight: 200.
- Full pronunciation must rank first.
- Mixed five-syllable abbreviation must be recallable.
- Short `ㄓㄨˊ` must not surface the brand term in the normal top 40.
- No large language model or meaningful memory increase.

---

### Task 1: Brand dictionary data and injection
**Files:**
- Create: `Resources/brand_words.csv`
- Create: `Tools/inject_dictionary_words.py`
- Modify: `Resources/dictionary.bin`
- Test: `Tests/test_brand_word.py`

- [ ] Write failing dictionary-data test.
- [ ] Run it and confirm brand term is absent.
- [ ] Add data-driven injector and brand CSV.
- [ ] Inject into bundled fallback dictionary.
- [ ] Re-run test.

### Task 2: Long-abbreviation soft recall
**Files:**
- Modify: `Core/ZYEngine.c`
- Modify: `App/ZYRuntime.mm`
- Modify: `Tests/test_engine.c`
- Create: `Tests/test_brand_recall_static.py`

- [ ] Write failing full/abbreviation/no-short-pollution tests.
- [ ] Add generic 5+ syllable abbreviation soft priority.
- [ ] Preserve engine priority when runtime adds learned preference.
- [ ] Expand runtime raw recall pool to 256.
- [ ] Re-run tests.

### Task 3: Release integration
**Files:**
- Modify: `run_core_tests.sh`
- Modify: `README.md`
- Modify: `App/Info.plist`

- [ ] Add tests to full suite.
- [ ] Document built-in brand term behavior.
- [ ] Bump to v0.1.22 / build 23.
- [ ] Run full suite and package ZIP.
