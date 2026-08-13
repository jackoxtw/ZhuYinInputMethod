# Idle Space and Caps-Lock Shift Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update keyboard handling so idle Space commits a literal space immediately and Shift+letter case follows Caps Lock only when no candidate is active.

**Architecture:** Keep all behavior in `ZYInputController.mm`. Add tiny helper logic for Latin casing and change only the idle branch of the Space key. Preserve candidate shortcut ordering so Shift+A–J continues to select candidates before Latin insertion.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, Python static regression tests.

## Global Constraints

- Base version: v0.1.32 / build 33.
- Do not change candidate shortcut behavior.
- Do not change dictionaries, learning, OpenCC, Composer, or panel behavior.

---

### Task 1: Add keyboard regression tests

**Files:**
- Create: `Tests/test_idle_space_caps_shift_static.py`
- Modify: `run_core_tests.sh`

- [ ] Write failing assertions for idle Space direct insertion.
- [ ] Write failing assertions for Caps Lock-only Shift casing with no candidates.
- [ ] Assert candidate Shift shortcuts occur before Latin handling and remain intact.
- [ ] Run the test and confirm RED.

### Task 2: Implement minimal keyboard behavior

**Files:**
- Modify: `App/ZYInputController.mm`

- [ ] Make idle Space call `insertText:@" "` directly.
- [ ] Normalize Shift+letter to lowercase then apply uppercase only when Caps Lock is set, only when `_candidateCount==0`.
- [ ] Preserve existing behavior when candidates are active.
- [ ] Run focused test and confirm GREEN.

### Task 3: Version and verify

**Files:**
- Modify release/version metadata and README as currently used by the project.

- [ ] Bump to v0.1.33 / build 34.
- [ ] Run full core/static/install-script regression suite.
- [ ] Zip release, extract cleanly, and repeat verification.
