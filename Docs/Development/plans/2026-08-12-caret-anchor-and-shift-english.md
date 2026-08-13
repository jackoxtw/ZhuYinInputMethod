# Caret Anchor and Shift English Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Anchor candidates to the marked-text caret and support temporary Shift English typing in Chinese mode.

**Architecture:** The input controller queries the client for the marked-text selection endpoint after it has set marked text. Its key-down handler reserves protected modifiers, selection shortcuts, and Chinese punctuation before inserting a Shift-modified ASCII letter as ordinary client text.

**Tech Stack:** Objective-C++, InputMethodKit, AppKit, shell regression checks.

## Global Constraints

- Candidate panel remains at the caret right-top with a 6 px gap and never moves over the caret.
- Command, Option, and Control events remain pass-through.
- Shift+number selection and Shift punctuation behavior remain unchanged.

---

### Task 1: Query the marked-text caret correctly

**Files:**
- Modify: `App/ZYInputController.mm:45-48`
- Modify: `Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 1: Write the failing check**

Require `firstRectForCharacterRange:NSMakeRange([self preeditText].length,0)` and prohibit the `NSNotFound` range in `clientRect:`.

- [ ] **Step 2: Run check and observe failure**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 3: Implement the caret range**

Request the end of `[self preeditText]` from the client, retain mouse-position fallback when the client does not support the selector or returns an empty rect.

- [ ] **Step 4: Run check and compile**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh && xcrun clang++ -fobjc-arc -std=c++17 -I"$PWD/Core" -I"$PWD/App" -c App/ZYInputController.mm -o /private/tmp/ZYInputController-caret.o`

### Task 2: Insert Shift English letters

**Files:**
- Modify: `App/ZYInputController.mm:124-151`
- Modify: `Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 1: Write the failing check**

Require an ASCII-letter predicate and `insertText:event.characters replacementRange:` branch after Shift candidate selection and Chinese punctuation handling.

- [ ] **Step 2: Run check and observe failure**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 3: Insert Shift English letters**

When Shift is down and `event.characters` is exactly one ASCII A-Z/a-z character, insert it through the client and return `YES`; do not alter composition or language state.

- [ ] **Step 4: Run full verification**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh && ./run_core_tests.sh && ./build_and_install.command`

- [ ] **Step 5: Commit**

Run:

    git add App/ZYInputController.mm Tests/check_objcpp_linkage_and_panel.sh docs/superpowers/specs/2026-08-12-caret-anchor-and-shift-english-design.md docs/superpowers/plans/2026-08-12-caret-anchor-and-shift-english.md
    git commit -m "fix: anchor candidates to caret and type Shift English"
