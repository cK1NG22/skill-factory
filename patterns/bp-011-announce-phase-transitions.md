# BP-011: Announce phase transitions

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Workflow & human-in-the-loop (Conditional — trait: `has_hitl`)

**Why:** In long workflows, users lose track of where they are. Explicit phase announcements keep them oriented and provide natural review checkpoints.

**When applicable:** Skills with user gates mid-flow (trait: `has_hitl`).

**Enforced by:** `skill-phase-designer`

**Correct:** `Announce: "Starting Phase 2: Solution Development. We'll generate 3–5 candidate solutions before committing to one."`

**Incorrect:** Skill silently transitions between phases; user can't tell what changed.
