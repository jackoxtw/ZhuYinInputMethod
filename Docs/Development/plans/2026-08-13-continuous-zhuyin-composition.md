# Continuous Zhuyin Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓逐音輸入法能把連續注音自動切成多詞候選，例如 `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` 直接得到 `今天天氣`，不必在「今天」後先按 Enter。

**Architecture:** `ZYEngine` 新增 prefix lookup 並回報 consumed codepoints；純 C `ZYComposer` 用最多 8 段、beam width 32 搜尋完整組句；`ZYRuntime` 合併單詞、組句與學習權重；`ZYInputController` 選中組句後拆回既有 `ZYPendingPiece`，因此沿用現有最終 Enter 學習流程。

**Tech Stack:** C11、Objective-C++/InputMethodKit、既有 binary dictionary、既有 ZYLearning。

## Global Constraints

- 一般候選仍最多 40 個，候選窗一般模式仍 2 行。
- 不改 `learning_A.dat / learning_B.dat` persistent layout。
- 不自動提交已匹配的前詞；最後 Enter 才正式送出並學習。
- 最多 8 個組句詞段，beam width 32，每個 offset 最多展開 12 個 prefix 候選。
- 既有 trailing partial syllable、adaptive learning、OpenCC、F9、Emoji／標點功能不可退化。

---

### Task 1: Prefix word lookup

**Files:**
- Modify: `Core/ZYEngine.h`
- Modify: `Core/ZYEngine.c`
- Modify: `Tests/test_engine.c`

**Interfaces:**
- Produces: `size_t zy_engine_lookup_prefix(ZYEngine*, const char*, ZYCandidate*, size_t)`
- Produces: `ZYCandidate.word_complete`, `ZYCandidate.consume_codepoints`

- [ ] **Step 1: Write failing tests** asserting that prefix lookup on `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` returns `今天` with `word_complete=1` and a consumed prefix shorter than the full query, while `ㄐㄧㄣㄊㄧㄢㄊ` can return a terminal partial edge after `今天`.
- [ ] **Step 2: Run `bash run_core_tests.sh` and verify the new assertions fail because the prefix API/metadata do not exist.**
- [ ] **Step 3: Refactor the pronunciation matcher to support full-query mode and prefix-query mode without changing existing `zy_engine_lookup()` behavior.**
- [ ] **Step 4: Run `bash run_core_tests.sh`; expect `test_engine: OK`.**

### Task 2: Pure-C beam composer

**Files:**
- Create: `Core/ZYComposer.h`
- Create: `Core/ZYComposer.c`
- Create: `Tests/test_composer.c`
- Modify: `run_core_tests.sh`
- Modify: `CMakeLists.txt`
- Modify: `build_and_install.command`

**Interfaces:**
- Consumes: `zy_engine_lookup_prefix()`
- Produces: `size_t zy_composer_lookup(ZYEngine*, const char*, ZYCandidate*, size_t)`
- `ZYCandidate.segment_count`, `segment_ids[8]`, `segment_consume_codepoints[8]`

- [ ] **Step 1: Write failing composer test**: `ㄐㄧㄣㄊㄧㄢㄊㄧㄢㄑㄧˋ` must return `今天天氣` as first composition and contain two dictionary segments; `ㄐㄧㄣㄊㄧㄢㄊ` must surface at least one composition beginning with `今天`.
- [ ] **Step 2: Compile/run only `test_composer`; verify it fails before `ZYComposer` exists.**
- [ ] **Step 3: Implement bounded beam search** with 8 segments, beam width 32, 12 outgoing prefix edges per state, segment penalty, dedupe, UTF-8 codepoint offsets, and no literal edges.
- [ ] **Step 4: Run `test_composer` and tune only the documented scoring constants until `今天天氣` outranks character-by-character segmentation.**
- [ ] **Step 5: Run full `bash run_core_tests.sh`.**

### Task 3: Runtime learning integration

**Files:**
- Modify: `App/ZYRuntime.mm`
- Modify: `App/ZYRuntime.h`
- Create: `Tests/test_composition_runtime_static.py`

**Interfaces:**
- Consumes: `zy_composer_lookup()`
- Produces: normal + composition candidates in `ZYRuntimeLookup()` with existing learning score model applied.

- [ ] **Step 1: Write static failing tests** requiring runtime to call `zy_composer_lookup`, apply constituent word learning bonuses, and merge/dedupe before final qsort.
- [ ] **Step 2: Run test and verify RED.**
- [ ] **Step 3: Implement composition merge and learning score adjustment without changing persistent learning structs.**
- [ ] **Step 4: Run static test and core suite.**

### Task 4: Controller expansion into learnable pieces

**Files:**
- Modify: `App/ZYInputController.mm`
- Create: `Tests/test_composition_controller_static.py`

**Interfaces:**
- Consumes: `ZYCandidate.segment_count`, `segment_ids`, `segment_consume_codepoints`
- Produces: one `ZYPendingPiece` per selected segment; existing `learnAndCommit:` learns constituents and combined phrase.

- [ ] **Step 1: Write failing static test** requiring composition branch in `appendPieceForCandidate:` and ensuring no call to learning occurs before `learnAndCommit:`.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement segment expansion**, slicing `_composition` by codepoints and filling pronunciation via `ZYRuntimeCandidatePron`.
- [ ] **Step 4: Verify static test and existing shortcut/candidate tests.**

### Task 5: Version, README, release verification

**Files:**
- Modify: `App/Info.plist`
- Modify: `README.md`
- Modify: `Tests/test_release_structure.py` only if version-aware assertions require it.

**Interfaces:**
- Produces: v0.1.15 / build 16 release documentation.

- [ ] **Step 1: Update version to `0.1.15` and build `16`.**
- [ ] **Step 2: Document continuous composition examples and limits.**
- [ ] **Step 3: Run `bash run_core_tests.sh`, all Python/static tests, `bash -n build_and_install.command`, `bash -n uninstall.command`, and Objective-C++ static checks.**
- [ ] **Step 4: Zip release, unzip to a fresh directory, rerun the same verification, and record SHA256.**
