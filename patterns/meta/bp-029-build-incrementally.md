# BP-029: Build incrementally — one piece deeply, never scaffold-then-fill

**Source:** `feedback-incremental-build-not-scaffold-first.md`; Carter's pushback in Phase 4 round 3
**Category:** Authoring discipline (Meta — factory dev process)

**Why:** Scaffolding all sub-skills as empty stubs hides unfinished work and removes review checkpoints. Each stage produces a working, committed, reviewable artifact — never a half-built skeleton.

**When applicable:** Adding any new sub-skill, archetype, or factory feature. Factory-internal PR discipline.

**Enforced by:** Stage cadence rules in `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md`; reviewer discipline.

**Correct:** Stage 3 ships `skill-spec-validator` end-to-end with fixtures, tests, integration. Stage 4 starts only after Stage 3 review.

**Incorrect:** Stage 0 creates 15 empty `skill-X/` dirs, then iterates filling each.
