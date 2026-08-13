# Memory Optimization v0.1.32 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove mouse diagnostic disk logging and reduce idle/candidate-panel memory without changing input quality or features.

**Architecture:** Keep the existing lazy candidate panel. When candidates disappear, hide and clear transient content immediately, then release the panel after a short idle delay unless it is reused. Cache immutable drawing attributes used on every candidate repaint. Remove all `/tmp/zhu-yin-mouse.log` code paths.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, Python static regression tests, native C core tests.

## Global Constraints

- Do not reduce dictionary coverage, candidate recall size, Composer behavior, learning, OpenCC, Emoji, or punctuation features.
- Do not introduce additional persistent disk writes.
- Keep candidate mouse interaction and auxiliary non-modal panels working.

---

### Task 1: Remove mouse diagnostics
- [ ] Add failing static test asserting no mouse log path/helpers remain.
- [ ] Remove mouse trace helpers/calls from candidate panel and input controller.
- [ ] Run focused and full tests.

### Task 2: Idle candidate-panel release
- [ ] Add failing static test for immediate transient-content clearing and delayed release.
- [ ] Add controller hide/schedule/cancel lifecycle helpers.
- [ ] Clear candidate view content and shrink to minimum height on hide.
- [ ] Run focused and full tests.

### Task 3: Candidate drawing caches
- [ ] Extend drawing regression test for immutable labels/font attribute caches.
- [ ] Cache shortcut list, candidate font dictionaries, and fixed control-label attributes.
- [ ] Run full tests and package verification.
