# Candidate Mouse Delegate Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every candidate-panel mouse click reach the active `ZYInputController` reliably while preserving non-activating keyboard focus behavior.

**Architecture:** `ZYCandidateView` will no longer point directly at the input controller. It sends actions to its owning `ZYCandidatePanel`; the panel holds the active `candidateDelegate` strongly and forwards actions. `ZYInputController` breaks the retain cycle in `inputControllerWillClose`. Mouse diagnostics extend through the panel and controller so a Mac runtime test can prove where an action succeeds or fails.

**Tech Stack:** Objective-C++, AppKit, InputMethodKit, Python static regression tests.

## Global Constraints
- Preserve `NSWindowStyleMaskNonactivatingPanel`, `becomesKeyOnlyIfNeeded=YES`, and `needsPanelToBecomeKey=NO`.
- Do not change candidate hit-testing coordinates or keyboard candidate selection behavior.
- Do not log composition text; diagnostics may log only action names, indices, booleans, and coordinates.
- Keep `/tmp/zhu-yin-mouse.log` bounded.

---

### Task 1: Lock delegate routing behavior
- [ ] Add a failing static test requiring View→Panel forwarding, strong panel delegate ownership, and cycle break on `inputControllerWillClose`.
- [ ] Run it and confirm RED.
- [ ] Implement the minimal routing architecture.
- [ ] Run it and confirm GREEN.

### Task 2: Extend controller diagnostics
- [ ] Add a failing static test requiring controller entry/result logging for candidate and clear-learning actions.
- [ ] Run it and confirm RED.
- [ ] Add bounded append-only controller logging with no text payload.
- [ ] Run it and confirm GREEN.

### Task 3: Release verification
- [ ] Run full regression suite.
- [ ] Bump version/build and README.
- [ ] Package ZIP, extract cleanly, rerun full suite and script syntax/permissions checks.
