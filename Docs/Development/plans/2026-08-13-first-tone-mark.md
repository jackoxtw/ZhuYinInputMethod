# Space First-Tone Mark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add optional explicit Mandarin first-tone mark `ˉ`, entered with Space, while preserving unmarked first tone, continuous composition, candidate selection, and shared learning identity.

**Architecture:** The engine recognizes `ˉ` as an explicit tone suffix only for dictionary syllables whose stored pronunciation is unmarked first tone. The composer treats `ˉ` as a legal syllable terminator. Runtime query hashing ignores `ˉ`, so marked and unmarked first-tone input share query-specific learning. InputController interprets Space contextually: append `ˉ` when the current composition ends in an untoned Bopomofo symbol; if the composition already ends in any tone mark, Space confirms the selected candidate.

**Tech Stack:** C99 core engine/composer, Objective-C++ InputMethodKit controller, Python static regression tests.

## Global Constraints

- `ㄊㄧㄢ` and `ㄊㄧㄢˉ` must resolve to the same first-tone dictionary candidates.
- Explicit `ˉ` must not match second/third/fourth/light-tone syllables as first tone.
- Query-specific learning must treat marked/unmarked first tone as the same query.
- Space appends `ˉ` only when the current composition ends in an untoned Bopomofo symbol.
- If the current composition already ends in `ˉ ˊ ˇ ˋ ˙`, Space keeps its candidate-confirm behavior.
- Existing continuous input without explicit first-tone marks remains valid.
- Existing F9, Emoji, punctuation, quick-help, adaptive layout, composition quality filtering, and learning behavior remain intact.

---

### Task 1: Engine explicit-first-tone semantics

**Files:**
- Modify: `Core/ZYEngine.c`
- Test: `Tests/test_engine.c`

**Interfaces:**
- Consumes: existing dictionary syllables with first tone stored without a tone suffix.
- Produces: `zy_engine_lookup()` and `zy_engine_match_pron_key()` treat query suffix `ˉ` as a full explicit first-tone match.

- [x] Add failing tests for `ㄊㄧㄢˉ -> 天`, exact match class 4, and non-match against `ㄊㄧㄢˊ`.
- [x] Run `./run_core_tests.sh` and confirm the first-tone assertion fails.
- [x] Add explicit-first-tone matching to dictionary-word and pronunciation-key matching.
- [x] Re-run engine tests and confirm green.

### Task 2: Composer first-tone boundaries

**Files:**
- Modify: `Core/ZYComposer.c`
- Test: `Tests/test_composer.c`

**Interfaces:**
- Consumes: engine prefix edges that include explicit `ˉ` in consumed codepoints.
- Produces: continuous composition can cross first-tone-marked syllable boundaries.

- [x] Add failing composition test for `ㄐㄧㄣˉㄊㄧㄢˉㄊㄧㄢˉㄑㄧˋ -> 今天天氣`.
- [x] Treat U+02C9 as a tone terminator in composer boundary parsing.
- [x] Re-run composer tests and confirm green.

### Task 3: Space behavior and normalized learning identity

**Files:**
- Modify: `App/ZYInputController.mm`
- Modify: `App/ZYRuntime.mm`
- Create: `Tests/test_first_tone_space_static.py`
- Modify: `run_core_tests.sh`

**Interfaces:**
- Produces: Space appends `ˉ` to untoned composition; a second Space after a tone confirms candidates; `ZYRuntimeQueryHash()` ignores `ˉ`.

- [x] Add static red tests for contextual Space handling and normalized query hash.
- [x] Implement `ZYCompositionNeedsFirstTone()` and update keyCode 49 handling.
- [x] Normalize `ZYRuntimeQueryHash()` by skipping UTF-8 U+02C9.
- [x] Add the static test to the full test runner and verify green.

### Task 4: Documentation, quick help, release, verification

**Files:**
- Modify: `App/ZYCandidatePanel.mm`
- Modify: `README.md`
- Modify: `App/Info.plist`

**Interfaces:**
- Produces: user-visible documentation consistently states Space = first tone / confirm after tone.

- [x] Update quick-help copy to show all five tones `ˉ ˊ ˇ ˋ ˙` and contextual Space behavior.
- [x] Update README shortcuts and first-tone examples.
- [x] Bump release to v0.1.19 / build 20.
- [x] Run the full test suite from the working tree.
- [x] Create final ZIP, extract it to a clean directory, run the full test suite again, and verify executable permissions.
