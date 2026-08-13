# Memory Diagnostic Modes Design

## Goal

Identify which per-key stage causes the observed ~100 MB transient memory spike without changing normal input behavior and without adding diagnostic disk writes.

## Modes

The input controller reads `MemoryDiagnosticMode` once from its `NSUserDefaults` domain when constructed.

- `0`: normal production path.
- `1`: callers still execute `setMarkedText:`; candidate refresh stops before `ZYRuntimeLookup()` and the candidate panel remains hidden.
- `2`: callers execute `setMarkedText:` and `ZYRuntimeLookup()`; candidate panel rendering/positioning remains hidden.
- `3`: full path, explicitly equivalent to mode 0 for controlled comparison.

Invalid values fall back to mode 0.

## Persistence and privacy

The input method only reads the preference. It does not emit logs, `/tmp` files, profiling files, or other diagnostic output. The user changes modes manually with `defaults`; because the mode is cached per controller, the input method process is restarted between measurements.

## Interpretation

- Mode 1 near 100 MB: marked-text/InputMethodKit/TextKit path dominates.
- Mode 1 low, mode 2 near 100 MB: Runtime lookup dominates.
- Modes 1 and 2 low, mode 3 near 100 MB: Candidate Panel/AppKit display path dominates.

## Regression constraints

Default mode 0 must preserve all existing behavior. Candidate ordering, learning, continuous composition, Space first tone, Caps Lock/Shift rules, panel lifecycle, dictionary formats, and memory optimizations remain unchanged.
