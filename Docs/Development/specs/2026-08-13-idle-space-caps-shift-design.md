# Idle Space and Caps-Lock Shift Input Design

**Goal:** Make idle Space insert a real space directly, and make Shift+letter output lowercase/uppercase according only to Caps Lock when no candidate is active.

## Behavior

- When Chinese mode is active and there is no composition, no pending piece, no candidate, and no special candidate mode, Space inserts `" "` directly into the client.
- Existing Space behavior during Zhuyin composition is unchanged: add explicit first tone `ˉ` when appropriate, otherwise choose the selected candidate when candidates exist.
- When no candidate is active, Shift+ASCII letter inserts Latin text directly: Caps Lock off => lowercase; Caps Lock on => uppercase. Shift itself does not change case.
- When candidates are active, existing Shift+1–0/A–J candidate shortcuts remain unchanged. Existing behavior for other shifted letters while candidates are present remains unchanged.
- No changes to dictionaries, learning, candidate ranking, OpenCC, or panel behavior.

## Testing

Static regression tests will assert direct idle-space insertion, Caps Lock driven casing, and preservation of candidate shortcuts.
