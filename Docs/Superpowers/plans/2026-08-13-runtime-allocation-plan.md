# Runtime Allocation Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove avoidable per-keystroke heap and Objective-C substring allocations from the composition lookup path.

**Architecture:** Keep dictionary lookup and candidate ranking unchanged. Introduce a reusable Composer workspace at Runtime scope and hash query segments directly from UTF-8 byte ranges instead of constructing temporary NSString substrings.

**Tech Stack:** C99 core, Objective-C++ Runtime, InputMethodKit/AppKit integration.

## Global Constraints

- Do not reduce candidate caps or dictionary coverage.
- Do not change ranking/learning semantics.
- Keep `zy_composer_lookup()` source-compatible.
- No diagnostic disk logging.

---

### Task 1: Reusable Composer workspace

**Files:**
- Modify: `Core/ZYComposer.h`
- Modify: `Core/ZYComposer.c`
- Modify: `App/ZYRuntime.mm`
- Test: `Tests/test_composer_workspace.c`

**Interfaces:**
- Produces: `ZYComposerWorkspace`, `zy_composer_workspace_init`, `zy_composer_workspace_dispose`, `zy_composer_lookup_with_workspace`.

- [ ] Write a test that performs repeated lookups with one workspace and compares results with normal composer lookup.
- [ ] Run it and confirm failure before the new API exists.
- [ ] Implement workspace allocation/growth once and reuse it.
- [ ] Route `ZYRuntimeLookup()` through one Runtime-owned workspace.
- [ ] Run composer and full core tests.

### Task 2: UTF-8 range query hashing

**Files:**
- Modify: `App/ZYRuntime.mm`
- Test: `Tests/test_runtime_allocation_static.py`

**Interfaces:**
- Produces: direct codepoint-range query hashing with first-tone normalization.

- [ ] Add a static regression test forbidding `substringWithRange:` in Runtime lookup and requiring range-hash helpers.
- [ ] Run it and confirm failure on v0.1.38.
- [ ] Compute UTF-8 codepoint byte offsets once per query and hash constituent ranges directly.
- [ ] Run composition/learning tests to verify ranking behavior remains unchanged.

### Task 3: Release/version verification

**Files:**
- Modify: `App/Info.plist`
- Modify: `README.md`
- Modify: `run_core_tests.sh`

- [ ] Add new tests to the regression runner.
- [ ] Bump version/build.
- [ ] Run full regression, linkage, installer and shell syntax checks.
- [ ] Zip, extract cleanly, and rerun key verification from the delivery archive.
