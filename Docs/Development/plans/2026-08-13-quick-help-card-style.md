# Quick Help Card Style Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the quick-help surface to visually match the non-modal clear-learning card while preserving all existing candidate-panel mouse behavior.

**Architecture:** Keep the existing lazy `ZYHelpPanel`, but replace its plain `NSTextField` content with a dedicated `ZYHelpView` that draws the card, title, shortcut pills, close affordances, and footer. Reuse the same non-activating panel behavior, elevation, rounded background, shadow, and positioning approach as `ZYClearLearningPanel` without sharing deletion logic.

**Tech Stack:** Objective-C++, AppKit/InputMethodKit, Python static regression tests.

## Global Constraints
- No `NSAlert` or `runModal`.
- Help remains non-modal and does not take text-input focus.
- Existing candidate mouse routing and clear-learning behavior must remain unchanged.
- Esc, top-right ×, and bottom Close all dismiss help.

### Task 1: Lock the help-card behavior with tests
- [ ] Add `Tests/test_quick_help_card_style_static.py` asserting custom help view, card styling, status-window elevation, `orderFrontRegardless`, and all three close paths.
- [ ] Run the new test and verify it fails on v0.1.28.

### Task 2: Implement the styled help card
- [ ] Add `ZYHelpView` drawing and mouse hit-testing in `App/ZYCandidatePanel.mm`.
- [ ] Update `toggleQuickHelp` to create the new view lazily and show it with `orderFrontRegardless` at `NSStatusWindowLevel+1`.
- [ ] Preserve `closeQuickHelp` so the InputController Esc path continues working.
- [ ] Update README and release version.
- [ ] Run full regression suite.
