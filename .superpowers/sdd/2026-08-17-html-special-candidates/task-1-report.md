Task 1 Report
Date: 2026-08-17
Commit: `cc5a955002e7db020b103b7da4445586c0d3f7ae` (`feat: add HTML special candidates`)

Changes
- Added `SPECIAL_CANDIDATES` to the HTML prototype with emoji and punctuation arrays aligned to `Platforms/macOS/App/ZYInputController.mm`.
- Added `state.specialMode`, `specialCandidates()`, `activeCandidates()`, `candidatePageSize()`, `openSpecialCandidates()`, `closeSpecialCandidates()`, `toggleSpecialCandidates()`, and `chooseSelectedCandidate()`.
- Updated candidate paging, movement, shortcut selection, rendering, and pointer selection to work against either normal candidates or special candidates.
- Routed Chinese-mode keyboard behavior for special candidates: backquote/quote openers, Escape/Backspace close-first behavior, Space/Enter selection, Shift-English close-first preservation, and close-before-`handleSymbol(sym)`.
- Added `Tests/test_html_special_candidates_static.py` and registered it in `run_core_tests.sh`.

RED
- Command: `python3 Tests/test_html_special_candidates_static.py`
- Result: failed as expected before implementation.
- Output summary:
  - Initial run errored because the test fixture assumed missing functions existed; I corrected the test to fail by assertion instead of setup error.
  - Verified red state after that: 5 failing assertions for missing special candidate data, helpers, keyboard routing, symbol-close behavior, and runner registration.

GREEN
- Commands:
  - `python3 Tests/test_html_special_candidates_static.py`
  - `python3 Tests/test_html_shift_english_static.py`
  - `python3 Tests/test_html_native_parity_static.py`
- Result: all passed after the HTML and runner changes.
- Output summary:
  - `Tests/test_html_special_candidates_static.py`: `Ran 5 tests ... OK`
  - `Tests/test_html_shift_english_static.py`: `test_html_shift_english_static: OK`
  - `Tests/test_html_native_parity_static.py`: `Ran 4 tests ... OK`

Full Verification
- Command: `./run_core_tests.sh`
- Result: passed.
- Output summary:
  - Native C core tests: OK
  - OpenCC / Taiwan dictionary / composition / quick-help / first-tone regressions: OK
  - `Tests/test_html_special_candidates_static.py`: `Ran 5 tests ... OK`
- Command: `git --no-pager diff --check -- 'Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html' 'Tests/test_html_special_candidates_static.py' 'run_core_tests.sh'`
- Result: passed with exit code 0.

Known Concerns
- Repository-wide `git diff --check` did not return in this tool session twice, so I used the same check scoped to the three Task 1 files and it passed cleanly.

Review Fix Round 1

Scope
- Fixed the special-candidate keyboard guard so only unshifted Backquote and Quote open special candidates.
- Tightened `Tests/test_html_special_candidates_static.py` so it requires `!e.shiftKey` in both guards and prevents the unguarded form from returning.

RED
- Command: `python3 Tests/test_html_special_candidates_static.py`
- Result: failed as expected against the previous HTML.
- Output summary:
  - `FAIL: test_keys_open_toggle_and_select_special_candidates`
  - Missing expected guarded string: `if(!e.shiftKey && e.code==='Backquote'){...}`

GREEN
- Commands:
  - `python3 Tests/test_html_special_candidates_static.py`
  - `python3 Tests/test_html_shift_english_static.py`
  - `python3 Tests/test_html_native_parity_static.py`
- Result: all passed after the guard fix.
- Output summary:
  - `Tests/test_html_special_candidates_static.py`: `Ran 5 tests ... OK`
  - `Tests/test_html_shift_english_static.py`: `test_html_shift_english_static: OK`
  - `Tests/test_html_native_parity_static.py`: `Ran 4 tests ... OK`
