# Memory Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce resident memory without removing input-method features.

**Architecture:** Break unnecessary ownership cycles, lazily allocate the candidate window, release auxiliary windows when closed, and reuse tiny drawing objects. Preserve all public behavior.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, C core, Python/static regression tests, shell build scripts.

## Global Constraints
- Official product name remains 「逐音輸入法」.
- Do not remove dictionary, learning, composition, OpenCC, Emoji, punctuation, mouse, or help features.
- Keep non-modal clear-learning flow.

---

### Task 1: Window ownership lifecycle
**Files:** `App/ZYCandidatePanel.h`, `App/ZYCandidatePanel.mm`, `Tests/test_memory_window_lifecycle_static.py`
- [ ] Write failing tests for weak delegate and auxiliary window release.
- [ ] Run tests and confirm RED.
- [ ] Implement weak delegate and explicit help/clear panel teardown.
- [ ] Run tests and confirm GREEN.

### Task 2: Lazy candidate panel
**Files:** `App/ZYInputController.mm`, `Tests/test_memory_window_lifecycle_static.py`
- [ ] Add failing tests for no panel allocation in init and lazy creation before display.
- [ ] Confirm RED.
- [ ] Add ensure/release candidate panel helpers and nil-safe callers.
- [ ] Confirm GREEN.

### Task 3: Drawing allocation reduction
**Files:** `App/ZYCandidatePanel.mm`, `Tests/test_memory_drawing_static.py`
- [ ] Add failing static test for shared paragraph/shortcut attributes outside candidate loop.
- [ ] Confirm RED.
- [ ] Reuse common drawing objects.
- [ ] Confirm GREEN.

### Task 4: Release packaging
**Files:** `App/Info.plist`, `README.md`, `run_core_tests.sh`
- [ ] Add new tests to runner and run full suite.
- [ ] Bump to v0.1.31 / build 32.
- [ ] Repackage, extract cleanly, rerun verification, checksum artifact.
