# Clear Learning Bottom Anchor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the destructive 「清除學習」 control visually isolated at the bottom of the candidate panel whenever the panel grows taller, while preserving the compact layout at minimum height.

**Architecture:** Candidate-panel control geometry remains owned by `ZYCandidateView`. Replace the fixed clear-learning rectangle with a rect derived from the current view height, so it keeps the existing position at the 110pt minimum height but follows the bottom edge when candidate rows increase panel height. Use the same computed rectangle for drawing and hit testing, and draw a separator only when enough vertical space exists between Help and Clear Learning.

**Tech Stack:** Objective-C++ / AppKit, Python static regression tests, existing shell/C regression suite.

## Global Constraints

- Preserve all v0.1.29 mouse routing and non-modal panel behavior.
- Preserve current 「繁／簡」 and 「說明」 positions.
- Do not change clear-learning confirmation semantics.
- At 110pt panel height, keep current effective clear-learning position.
- At taller heights, 「清除學習」 must stay 6pt from the bottom edge.
- Drawing and mouse hit-testing must use the same computed rectangle.

---

### Task 1: Bottom-anchor candidate-panel destructive control

**Files:**
- Modify: `App/ZYCandidatePanel.mm`
- Create: `Tests/test_clear_learning_bottom_anchor_static.py`
- Modify: `run_core_tests.sh`

**Interfaces:**
- Consumes: `ZYCandidateView.bounds`
- Produces: `-clearLearningRect`, the single source of truth for drawing and hit testing.

- [ ] **Step 1: Write the failing static regression test**

Require a dynamic `clearLearningRect` based on `NSHeight(self.bounds)`, require both drawing and `mouseDown:` to use it, and forbid the old fixed `NSMakeRect(732,86,48,18)` duplicate.

- [ ] **Step 2: Run the test and verify it fails**

Run: `python3 Tests/test_clear_learning_bottom_anchor_static.py`
Expected: FAIL because v0.1.29 hard-codes y=86 in both drawing and hit-testing.

- [ ] **Step 3: Implement minimal geometry change**

Add `scriptRect`, `helpRect`, and dynamic `clearLearningRect` accessors. Return `NSMakeRect(732, MAX(86.0, NSHeight(self.bounds)-24.0), 48, 18)` for clear learning. Reuse those accessors in drawing and hit-testing. Draw a subtle separator above the destructive control only when the gap from Help is at least 18pt.

- [ ] **Step 4: Run focused and full regressions**

Run: `python3 Tests/test_clear_learning_bottom_anchor_static.py && ./run_core_tests.sh`
Expected: PASS.

- [ ] **Step 5: Bump release and package**

Update to v0.1.30 / build 31, update README control-layout description, package ZIP, re-extract into a clean directory, rerun the full suite and shell syntax checks.
