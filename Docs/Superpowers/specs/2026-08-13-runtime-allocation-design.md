# Runtime Allocation Design

**Goal:** Reduce the per-keystroke transient allocation peak without changing candidate quality, dictionary contents, learning behavior, or UI behavior.

## Findings

- `zy_engine_lookup()` already returns fixed-size C `ZYCandidate` records; the first 256 raw candidates do not create Objective-C strings.
- Only the displayed page (normally at most 20 candidates) is converted to `NSString` in `ZYCandidatePanel`.
- `zy_composer_lookup()` allocates and frees its beam/count workspace on every lookup.
- `ZYRuntimeLookup()` creates an `NSString` for the full query and substring `NSString` objects for constituent learning-query hashes.

## Design

1. Add an explicit reusable `ZYComposerWorkspace` owned by `ZYRuntime` and reused across lookups. The existing public `zy_composer_lookup()` remains as a compatibility wrapper for tests/other callers.
2. Replace Runtime's Objective-C substring hashing with direct UTF-8 codepoint-range hashing. Explicit first-tone U+02C9 continues to be ignored exactly as in `ZYRuntimeQueryHash()`.
3. Preserve all ranking, composition-quality windows, candidate caps, learned phrase handling, and final displayed candidate conversion.
4. Dispose the reusable Composer workspace when Runtime is shut down if a shutdown path exists; otherwise the workspace stays bounded to the maximum query size and is reused for process lifetime.

## Success criteria

- No `substringWithRange:` in `ZYRuntimeLookup()`.
- Runtime path uses `zy_composer_lookup_with_workspace()` with one reusable workspace.
- Repeated workspace lookups return identical candidates to the compatibility lookup.
- All existing native and static regression tests pass.
