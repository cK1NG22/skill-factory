# BP-028: BLOCKER convention — sub-skills never silently fail

**Source:** Plan §Data contract
**Category:** Hands-off operation (Meta — factory sub-skill discipline)

**Why:** A sub-skill that hits ambiguity it can't resolve writes `BLOCKER: <question>` as the first line of `notes.md`. Driver detects, exits cleanly to gap-report (treats as validator miss), and the validator improves on next run. No silent failures, no half-done outputs.

**When applicable:** Every factory sub-skill. Factory-internal; not applied to client skills.

**Enforced by:** `skill-compliance-gate` (rejects outputs with `BLOCKER:` present); driver routing logic.

**Correct:** Sub-skill blocked on missing field writes `BLOCKER: spec.outputs.path is unspecified — required for transformation archetype.` Exits.

**Incorrect:** Sub-skill guesses, produces output, downstream compliance fails, root cause buried.
