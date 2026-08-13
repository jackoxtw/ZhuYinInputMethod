# Memory Diagnostic Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add memory-only diagnostic modes that isolate marked-text update, runtime lookup, and candidate-panel display so macOS Activity Monitor can identify the source of the per-key memory spike.

**Architecture:** Read one integer diagnostic mode from `NSUserDefaults` when `ZYInputController` is created. Keep normal mode unchanged; mode 1 performs marked-text updates but skips lookup/panel, mode 2 performs marked-text plus lookup but suppresses panel, and mode 3 explicitly runs the normal full path. No diagnostic log files or per-key persistence are added.

**Tech Stack:** Objective-C++, InputMethodKit/AppKit, Python static regression tests, existing shell/C test harness.

## Global Constraints

- Default mode `0` must preserve normal behavior.
- Mode `1`: marked text only; no `ZYRuntimeLookup`, no Candidate Panel display.
- Mode `2`: marked text + `ZYRuntimeLookup`; no Candidate Panel display.
- Mode `3`: full normal path, equivalent to mode 0 for comparison.
- Diagnostic implementation must not write logs or other files.
- Existing input behavior, learning, candidate ordering, panel lifecycle, Space/Caps Lock behavior, and dictionary data must remain unchanged in normal mode.

---

### Task 1: Add diagnostic mode routing

**Files:**
- Modify: `App/ZYInputController.mm`
- Test: `Tests/test_memory_diagnostic_modes_static.py`

**Interfaces:**
- Consumes: `NSUserDefaults` integer key `MemoryDiagnosticMode`.
- Produces: cached `_memoryDiagnosticMode` and routing inside `refreshCandidates:`.

- [ ] **Step 1: Write the failing static test**
- [ ] **Step 2: Run the test and verify it fails because modes are absent**
- [ ] **Step 3: Add enum/key/cache and route modes 1/2 before panel refresh**
- [ ] **Step 4: Run the diagnostic test and existing input-controller tests**

### Task 2: Document test procedure and release

**Files:**
- Modify: `README.md`
- Modify: `App/Info.plist`
- Modify: `run_core_tests.sh`

**Interfaces:**
- Produces: v0.1.40 / build 41 and exact `defaults` commands for modes 0–3.

- [ ] **Step 1: Add the diagnostic regression test to the main test runner**
- [ ] **Step 2: Document commands and restart requirement**
- [ ] **Step 3: Update version/build**
- [ ] **Step 4: Run full verification and verify a clean extracted ZIP**
