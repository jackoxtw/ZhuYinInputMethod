# System Input Method Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install exactly one copy of 逐音輸入法 at `/Library/Input Methods/逐音輸入法.app` and remove legacy per-user copies.

**Architecture:** Shell scripts retain their existing build and LaunchServices behavior but treat the system-level bundle as the sole canonical destination. User-level paths are migration-cleanup targets only. Documentation describes the administrator authentication required by the scripts.

**Tech Stack:** Bash, macOS `sudo`, LaunchServices, shell integration test.

## Global Constraints

- Keep `set -euo pipefail` in both scripts.
- Do not change the input method bundle ID or input source ID.
- Do not write to `com.apple.HIToolbox` preferences.

---

### Task 1: Exercise canonical system-level installation

**Files:**
- Create: `Tests/test_install_destinations.sh`
- Modify: `build_and_install.command:50-70`
- Modify: `uninstall.command:1-4`
- Modify: `README.md:18-32`

**Interfaces:**
- Consumes: installation scripts executed as text artifacts.
- Produces: scripts whose only live installation target is `/Library/Input Methods/逐音輸入法.app`.

- [x] **Step 1: Write the failing integration test**

Create a shell test that copies the project to a temporary directory, replaces `sudo` and macOS command wrappers with recording executables in `PATH`, runs each script, and asserts the recorded `cp`, `rm`, `lsregister`, and `open` arguments name the canonical system path while legacy user paths are used only for removal.

- [x] **Step 2: Run test to verify it fails**

Run: `bash Tests/test_install_destinations.sh`

Expected: FAIL because the installer copies to `$HOME/Library/Input Methods/逐音輸入法.app`.

- [x] **Step 3: Implement the minimal script changes**

Set `DEST` to `/Library/Input Methods/逐音輸入法.app`; use `sudo mkdir`, `sudo rm`, and `sudo cp` for system-level mutations; remove legacy user-level bundles before registration; unregister the old user-level bundle; update uninstall to remove both copies; update README location and privilege wording.

- [x] **Step 4: Run the integration test to verify it passes**

Run: `bash Tests/test_install_destinations.sh`

Expected: PASS with a zero exit status.

- [x] **Step 5: Run existing core checks**

Run: `./run_core_tests.sh`

Expected: all existing C core tests pass.

- [ ] **Step 6: Commit**

Run:

    git add build_and_install.command uninstall.command README.md Tests/test_install_destinations.sh docs/superpowers/specs/2026-08-12-system-input-method-install-design.md docs/superpowers/plans/2026-08-12-system-input-method-install.md
    git commit -m "fix: install input method only at system level"
