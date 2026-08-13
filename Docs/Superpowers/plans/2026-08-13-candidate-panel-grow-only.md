# Candidate Panel Grow-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent repeated candidate-window shrinking and backing-store reallocations during one active composition.

**Architecture:** Keep the existing adaptive candidate layout calculations. Change only the window-resize policy: visible panels grow-only; hidden panels may resize to the next composition's desired height. Do not resize during `orderOut:`.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, Python static regression tests.

## Global Constraints

- Do not change dictionary, ranking, candidate recall, paging, learning, mouse behavior, or the 2-second idle release.
- Preserve minimum panel height 110pt and width 786pt.

---

### Task 1: Lock resize policy with a regression test

**Files:**
- Create: `Tests/test_candidate_grow_only_static.py`
- Modify: `run_core_tests.sh`

- [ ] Write a failing static test for visible grow-only behavior and no resize in `orderOut:`.
- [ ] Run it and verify it fails on v0.1.36.

### Task 2: Implement grow-only resize

**Files:**
- Modify: `App/ZYCandidatePanel.mm`

- [ ] Use desired height directly when hidden.
- [ ] Use `MAX(current.height, desiredHeight)` when visible.
- [ ] Remove `resizeForRows:2` from `orderOut:`.
- [ ] Run focused and full regression tests.

### Task 3: Version and package

**Files:**
- Modify: `App/Info.plist`
- Modify: `README.md`

- [ ] Bump version/build.
- [ ] Package ZIP, extract cleanly, rerun verification.
