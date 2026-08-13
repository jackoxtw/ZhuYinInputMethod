# Special Candidate Five Rows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Emoji and punctuation candidates display up to five rows / 50 items per page while keeping normal Zhuyin candidates at two rows / 20 items.

**Architecture:** Keep one candidate panel. The input controller chooses page size by candidate mode; the panel chooses row count and content height by presentation mode. No changes to engine, learning, or OpenCC conversion.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, Python static regression tests.

## Global Constraints
- Normal Zhuyin candidate UI stays 2 rows × 10.
- Special candidate UI is 1–5 rows × 10, at most 50 per page.
- Existing F9/script toggle, caret placement, learning behavior, and OpenCC flow remain unchanged.

---

### Task 1: Paging regression
**Files:**
- Modify: `Tests/test_shortcuts_static.py`
- Modify: `App/ZYInputController.mm`

- [ ] Add failing assertions for special page size 50 and normal page size 20.
- [ ] Run the static test and confirm failure.
- [ ] Add a mode-dependent page-size helper and use it in `refreshPanel`, Page Up, and Page Down.
- [ ] Re-run the static test.

### Task 2: Dynamic candidate rows
**Files:**
- Modify: `Tests/test_shortcuts_static.py`
- Modify: `App/ZYCandidatePanel.mm`

- [ ] Add failing assertions for max 5 rows, normal fixed 2 rows, 50 special words, and 5-row mouse selection.
- [ ] Run and confirm failure.
- [ ] Add view row state, mode-aware update path, dynamic content height, and 5-row hit testing.
- [ ] Re-run tests.

### Task 3: F9 hint and version / full verification
**Files:**
- Modify: `App/ZYCandidatePanel.mm`
- Modify: `App/Info.plist`
- Modify: `README.md`

- [ ] Add a small `F9` hint at the upper-left of the existing script button without replacing the main `繁/簡` label.
- [ ] Bump to v0.1.10 build 11.
- [ ] Run the complete project regression suite and shell syntax checks.
- [ ] Package ZIP, re-extract it, and run the same verification from the extracted delivery tree.
