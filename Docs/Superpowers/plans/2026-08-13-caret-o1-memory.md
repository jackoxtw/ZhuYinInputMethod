# Caret O(1) Lookup Memory Implementation Plan

**Goal:** Make candidate caret lookup fixed-cost and promptly drain temporary AppKit objects.

1. Add a static regression test requiring one final-character IMK lookup, no backward preedit loop, and a local autorelease pool.
2. Update `clientRect:` to perform one IMK line-height query followed by existing range/AX/cache fallbacks.
3. Update the older candidate-position regression to prohibit the removed backward scan.
4. Add the new regression to `run_core_tests.sh`.
5. Bump release to v0.1.38 / build 39, document the change, and run full regressions plus packaging verification.
