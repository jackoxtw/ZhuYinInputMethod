# Cross-Platform Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the project so macOS and Windows share one C99 input engine and binary resources while retaining separate native input-method adapters.

**Architecture:** `Shared/Core` owns deterministic query, composition, learning and conversion behavior; `Shared/Resources` owns all shared runtime data. `Platforms/macOS` contains InputMethodKit/AppKit and packaging, while `Platforms/Windows` contains a C++17 TSF scaffold that links the same Shared Core without duplicating logic.

**Tech Stack:** C99, C++17, Objective-C++, InputMethodKit/AppKit, Microsoft TSF, CMake, Python 3, GitHub Actions.

## Global Constraints

- Shared source files compile as C99 and must not include Cocoa, InputMethodKit, Windows SDK, COM, Objective-C, or C++ headers.
- `dictionary.bin`, `t2s.bin`, candidate IDs and learning-file formats remain byte-compatible between platforms.
- macOS minimum deployment target remains 12.0 and v0.1.47 Release packaging must still pass signature, installer and ZIP checks.
- Windows uses C++17 and TSF; this plan creates a buildable scaffold, not a distributable Windows IME.
- Existing behavior and candidate ordering must not change solely because files moved.

---

### Task 1: Establish shared source and resource roots

**Files:**
- Move: `Core/*` → `Shared/Core/*`
- Move: `Resources/*` → `Shared/Resources/*`
- Move: `Tools/*` → `Shared/Tools/*`
- Modify: `CMakeLists.txt`
- Modify: `run_core_tests.sh`
- Create: `Tests/test_shared_platform_boundary.py`

**Interfaces:**
- Produces include root `Shared/Core` and data root `Shared/Resources`.
- Produces `ZY_*` C APIs unchanged from their current headers.
- Consumed by macOS and Windows CMake targets in later tasks.

- [ ] **Step 1: Write the failing shared-boundary test**

```python
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for source in (root / 'Shared/Core').glob('*.[ch]'):
    text = source.read_text(encoding='utf-8')
    assert '#import' not in text
    assert 'Cocoa/' not in text
    assert 'windows.h' not in text.lower()
assert (root / 'Shared/Resources/dictionary.bin').is_file()
assert (root / 'Shared/Resources/t2s.bin').is_file()
```

- [ ] **Step 2: Run the boundary test before moving files**

Run: `python3 Tests/test_shared_platform_boundary.py`

Expected: FAIL because `Shared/Core` and `Shared/Resources` do not exist.

- [ ] **Step 3: Move only the shared ownership directories**

```bash
git mv Core Shared/Core
git mv Resources Shared/Resources
git mv Tools Shared/Tools
```

Update every path in `CMakeLists.txt` and `run_core_tests.sh` from `Core/`, `Resources/` and `Tools/` to its `Shared/` equivalent. Preserve source names and public C headers exactly.

- [ ] **Step 4: Verify shared-core and macOS CMake references**

Run: `python3 Tests/test_shared_platform_boundary.py && rg -n 'Shared/(Core|Resources|Tools)' CMakeLists.txt run_core_tests.sh`

Expected: PASS; CMake and test runner refer only to shared roots for engine/data/tool paths.

- [ ] **Step 5: Commit the shared-root migration**

```bash
git add Shared CMakeLists.txt run_core_tests.sh Tests/test_shared_platform_boundary.py
git commit -m "refactor: move shared engine and resources"
```

### Task 2: Isolate the macOS platform implementation

**Files:**
- Move: `App/*` → `Platforms/macOS/App/*`
- Move: `Packaging/*` → `Platforms/macOS/Packaging/*`
- Move: `build_and_install.command` → `Platforms/macOS/scripts/build_and_install.command`
- Move: `uninstall.command` → `Platforms/macOS/scripts/uninstall.command`
- Move: `建立Release.command` → `Platforms/macOS/scripts/建立Release.command`
- Create: root `build_and_install.command` compatibility launcher
- Create: `Tests/test_macos_layout_static.py`

**Interfaces:**
- Consumes `Shared/Core/*.h` and `Shared/Resources/*`.
- Produces the existing root command entrypoint, forwarding all parameters to the macOS script.
- Produces `Platforms/macOS/App/ZYRuntime.mm` as the only Objective-C++ runtime bridge.

- [ ] **Step 1: Write the failing macOS layout test**

```python
from pathlib import Path

root = Path(__file__).resolve().parents[1]
assert (root / 'Platforms/macOS/App/ZYInputController.mm').is_file()
assert (root / 'Platforms/macOS/Packaging/安裝逐音輸入法.command').is_file()
launcher = (root / 'build_and_install.command').read_text(encoding='utf-8')
assert 'Platforms/macOS/scripts/build_and_install.command' in launcher
```

- [ ] **Step 2: Run the macOS layout test before moving files**

Run: `python3 Tests/test_macos_layout_static.py`

Expected: FAIL because `Platforms/macOS` does not exist.

- [ ] **Step 3: Move platform-only files and add the launcher**

```bash
git mv App Platforms/macOS/App
git mv Packaging Platforms/macOS/Packaging
git mv build_and_install.command Platforms/macOS/scripts/build_and_install.command
git mv uninstall.command Platforms/macOS/scripts/uninstall.command
git mv 建立Release.command Platforms/macOS/scripts/建立Release.command
```

Create a root executable launcher that resolves its own directory and uses `exec` to forward `"$@"` to `Platforms/macOS/scripts/build_and_install.command`. Update all internal script paths to use `Platforms/macOS/App`, `Platforms/macOS/Packaging`, `Shared/Resources` and `Shared/Tools`.

- [ ] **Step 4: Verify the unchanged macOS build contract**

Run: `python3 Tests/test_macos_layout_static.py && ./build_and_install.command --release-only`

Expected: static layout test passes and a signed Release directory is recreated under `Release/逐音輸入法-v0.1.47`.

- [ ] **Step 5: Commit the macOS isolation**

```bash
git add Platforms build_and_install.command CMakeLists.txt Tests/test_macos_layout_static.py
git commit -m "refactor: isolate macOS platform layer"
```

### Task 3: Add a Windows TSF build scaffold

**Files:**
- Create: `Platforms/Windows/Ime/ZhuyinTextService.h`
- Create: `Platforms/Windows/Ime/ZhuyinTextService.cpp`
- Create: `Platforms/Windows/CMakeLists.txt`
- Create: `Platforms/Windows/README.md`
- Create: `Tests/test_windows_scaffold_static.py`

**Interfaces:**
- Consumes `Shared/Core/ZYEngine.h`, `Shared/Core/ZYLearning.h`, `Shared/Core/ZYConversion.h`.
- Produces a `ZhuyinWindowsCoreBridge` C++17 class whose constructor accepts resource directory and whose methods expose `lookup`, `commitCandidate`, and `reset` without UI ownership.
- Windows TSF UI will later call this bridge; it must not contain dictionary or learning algorithms.

- [ ] **Step 1: Write the failing Windows scaffold test**

```python
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cmake = (root / 'Platforms/Windows/CMakeLists.txt').read_text(encoding='utf-8')
bridge = (root / 'Platforms/Windows/Ime/ZhuyinTextService.cpp').read_text(encoding='utf-8')
assert 'Shared/Core/ZYEngine.c' in cmake
assert '#include "ZYEngine.h"' in bridge
assert 'InputMethodKit' not in bridge
```

- [ ] **Step 2: Run the Windows scaffold test before implementation**

Run: `python3 Tests/test_windows_scaffold_static.py`

Expected: FAIL because the Windows scaffold files do not exist.

- [ ] **Step 3: Implement the minimal TSF-ready bridge**

Define `ZhuyinWindowsCoreBridge` in C++17 with value-owned Core state, resource-directory configuration and a non-UI candidate result vector. Include TSF headers only in a future `TextService` adapter file; keep this bridge platform-neutral except for Windows path conversion at its outermost constructor.

Create `Platforms/Windows/CMakeLists.txt` with `if(NOT WIN32) message(FATAL_ERROR ...) endif()`, `CMAKE_C_STANDARD 99`, `CMAKE_CXX_STANDARD 17`, a static `ZhuyinWindowsCore` target that compiles the five `Shared/Core/*.c` units, and a `ZhuyinTextService` target linked with `ole32`, `uuid` and `msctf`.

- [ ] **Step 4: Verify scaffold isolation**

Run: `python3 Tests/test_windows_scaffold_static.py`

Expected: PASS. On macOS, do not execute the Windows CMake target; its README documents the Visual Studio 2022 / Windows SDK command.

- [ ] **Step 5: Commit the Windows scaffold**

```bash
git add Platforms/Windows Tests/test_windows_scaffold_static.py
git commit -m "feat: add Windows TSF core scaffold"
```

### Task 4: Make tests and documentation platform-aware

**Files:**
- Move: Core C tests and platform-neutral Python tests into `Shared/Tests/`
- Modify: `run_core_tests.sh`
- Modify: `README.md`
- Modify: `一般使用者安裝說明.md`
- Modify: `Docs/Development/specs/2026-08-14-cross-platform-layout-design.md`
- Create: `Tests/test_cross_platform_paths_static.py`

**Interfaces:**
- Consumes the directory roots created in Tasks 1–3.
- Produces one root test entrypoint that runs Shared tests on both platforms and adds platform-specific tests only on their native OS.

- [ ] **Step 1: Write the failing path-consistency test**

```python
from pathlib import Path

root = Path(__file__).resolve().parents[1]
readme = (root / 'README.md').read_text(encoding='utf-8')
runner = (root / 'run_core_tests.sh').read_text(encoding='utf-8')
assert 'Shared/Core' in readme
assert 'Platforms/macOS' in readme
assert 'Platforms/Windows' in readme
assert 'Shared/Tests' in runner
```

- [ ] **Step 2: Run the path-consistency test before documentation migration**

Run: `python3 Tests/test_cross_platform_paths_static.py`

Expected: FAIL because README and runner still describe the pre-refactor paths.

- [ ] **Step 3: Move tests by ownership and update documentation**

Move only engine, dictionary, learning, composer and conversion tests to `Shared/Tests`; retain InputMethodKit, Release, app icon, installer and candidate-panel static tests under `Tests/macOS`. Update the root runner to use `Shared/Tests` for all systems and conditionally execute `Tests/macOS` only when `uname -s` is `Darwin`.

Update README’s directory tree and build sections: explain Shared Core is identical for macOS and Windows, name InputMethodKit and TSF as separate adapters, and state that Windows is an early scaffold rather than a finished installer. Keep the general macOS user guide focused on its installed Release.

- [ ] **Step 4: Run full native verification**

Run: `./run_core_tests.sh && ./build_and_install.command --release-only && python3 Tests/test_release_package.py && codesign --verify --deep --strict 'Release/逐音輸入法-v0.1.47/逐音輸入法.app'`

Expected: shared tests pass, macOS Release is rebuilt, package test passes and the signed App validates.

- [ ] **Step 5: Commit tests and documentation**

```bash
git add Shared/Tests Tests/macOS run_core_tests.sh README.md 一般使用者安裝說明.md Docs/Development/specs/2026-08-14-cross-platform-layout-design.md Tests/test_cross_platform_paths_static.py
git commit -m "docs: document shared macOS and Windows layout"
```
