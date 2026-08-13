# Candidate Panel Grow-Only Memory Design

**Goal:** Reduce transient AppKit backing-store churn while typing without changing candidate count, layout rules, ranking, or paging.

**Design:** While the candidate panel is visible, `resizeForRows:` may increase content height but must not shrink it. When the panel is hidden, a later candidate update may resize it once to the new composition's required height before showing. Hiding the panel clears candidate data but does not resize the window; the existing 2-second idle release still closes and frees the panel.

**Constraints:** Keep the 786pt width, current row-height/column rules, 20 normal candidates, special candidate paging, mouse hit-testing, and 2-second idle release unchanged.

**Verification:** Static regression test must prove visible-panel height uses `MAX(current.height, desiredHeight)`, hidden panels can use desired height directly, and `orderOut:` does not call `resizeForRows:`.
