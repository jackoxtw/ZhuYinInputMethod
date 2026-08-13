# Icon, Shortcuts, and Candidate Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the supplied App icon, pass through system-modifier shortcuts, and place the candidate panel to the upper right of the caret.

**Architecture:** The installer generates `AppIcon.icns` from the source PNG during its local `/private/tmp` build and bundles it before signing. The input controller exits early for Command, Option, or Control key-down events. The candidate panel calculates a right-of-caret, above-caret origin then clamps only to its screen's visible frame.

**Tech Stack:** Bash, macOS `sips` and `iconutil`, Objective-C++, AppKit, shell checks.

## Global Constraints

- Use `icon/icon.png` as the only icon source.
- Do not change the input method bundle ID or input source ID.
- Command, Option, and Control shortcut events must reach the client App.
- Candidate panel must not cover the caret rectangle.

---

### Task 1: Bundle the App icon

**Files:**
- Modify: `build_and_install.command`
- Modify: `App/Info.plist`
- Modify: `Tests/test_install_destinations.sh`

- [ ] **Step 1: Write the failing checks**

Require the icon source, iconset size generation, `iconutil -c icns`, bundle copy, and `CFBundleIconFile` reference.

- [ ] **Step 2: Run the checks and observe failure**

Run: `bash Tests/test_install_destinations.sh`

- [ ] **Step 3: Generate and bundle `AppIcon.icns`**

Create 16, 32, 128, 256, 512 and 1024 pixel iconset variants from `icon/icon.png`; run `iconutil`; copy `AppIcon.icns` to bundle Resources before codesigning; set `CFBundleIconFile` and the three input-method icon file values.

- [ ] **Step 4: Run the checks and build verification**

Run: `bash Tests/test_install_destinations.sh && ./build_and_install.command`

Expected: checks pass and build bundle contains a valid `AppIcon.icns`.

### Task 2: Preserve system shortcuts and relocate the candidate panel

**Files:**
- Modify: `App/ZYInputController.mm`
- Modify: `App/ZYCandidatePanel.mm`
- Modify: `Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 1: Write failing source-level behavior checks**

Require an early `NSEventModifierFlagCommand | NSEventModifierFlagOption | NSEventModifierFlagControl` mask return and a candidate origin computed from `NSMaxX(rect)+6` and `NSMaxY(rect)+6`.

- [ ] **Step 2: Run the checks and observe failure**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh`

- [ ] **Step 3: Implement the minimal event and geometry changes**

Return `NO` before Shift/candidate handling when the protected modifier mask is present. Compute the panel lower-left at caret-right and caret-top, clamp to the visible screen while retaining a gap from the caret when the right side has room.

- [ ] **Step 4: Run all checks**

Run: `bash Tests/check_objcpp_linkage_and_panel.sh && ./run_core_tests.sh && bash Tests/test_install_destinations.sh`

- [ ] **Step 5: Commit**

Run:

    git add App/Info.plist App/ZYInputController.mm App/ZYCandidatePanel.mm build_and_install.command Tests/check_objcpp_linkage_and_panel.sh Tests/test_install_destinations.sh docs/superpowers/specs/2026-08-12-icon-shortcuts-candidate-panel-design.md docs/superpowers/plans/2026-08-12-icon-shortcuts-candidate-panel.md
    git commit -m "feat: add input method icon and shortcut handling"
