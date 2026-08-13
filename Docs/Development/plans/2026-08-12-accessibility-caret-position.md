# Accessibility Caret Position Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Position the candidate panel using the focused text field's Accessibility caret bounds.

**Architecture:** A small helper isolates AX lookup and coordinate conversion. The input controller asks the helper first, retains InputMethodKit and mouse fallbacks, and the build system links ApplicationServices.

**Tech Stack:** Objective-C++, ApplicationServices Accessibility API, AppKit, Bash.

## Global Constraints

- AX authorization is optional; lack of authorization must not prevent typing.
- Candidate panel remains right-top of the returned caret rect.
- Do not alter input engine or shortcut behavior.

---

### Task 1: Add AX caret lookup

**Files:**
- Create: `App/ZYAccessibilityCaret.h`
- Create: `App/ZYAccessibilityCaret.mm`
- Modify: `App/ZYInputController.mm`
- Modify: `Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 1: Write failing checks**

Require the helper to request `kAXFocusedUIElementAttribute`, `kAXSelectedTextRangeAttribute`, `kAXBoundsForRangeParameterizedAttribute`, and the controller to prefer `ZYAccessibilityCaretRect()`.

- [ ] **Step 2: Run check to observe failure**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 3: Implement AX lookup and fallbacks**

Use the focused element's selected range to fetch a bounds value; convert its display-local AX coordinates to AppKit coordinates; return `NSZeroRect` on every AX failure. Use it before client and mouse fallback in `clientRect:`.

- [ ] **Step 4: Compile and run checks**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh && xcrun clang++ -fobjc-arc -std=c++17 -framework ApplicationServices -I"$PWD/App" -c App/ZYAccessibilityCaret.mm -o /private/tmp/ZYAccessibilityCaret.o`

### Task 2: Link and package the helper

**Files:**
- Modify: `build_and_install.command`
- Modify: `CMakeLists.txt`

- [ ] **Step 1: Write failing checks**

Require helper compilation and `-framework ApplicationServices` in both build paths.

- [ ] **Step 2: Run check to observe failure**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 3: Link ApplicationServices and build helper**

Add the helper source to both build paths and ApplicationServices to both link lists.

- [ ] **Step 4: Verify full build and tests**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh && ./run_core_tests.sh && ./build_and_install.command`
