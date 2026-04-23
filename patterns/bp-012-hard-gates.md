# BP-012: Hard gates ("Do NOT proceed until…")

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Workflow & human-in-the-loop (Conditional — trait: `has_hitl`)

**Why:** After every checkpoint where skipping ahead would be costly, an explicit gate prevents premature progression. Especially important in long workflows.

**When applicable:** Skills with user gates mid-flow (trait: `has_hitl`). Density scales with reversibility — high-stakes steps need more gates.

**Enforced by:** `skill-phase-designer`

**Correct:** `Do NOT proceed to Phase 3 until the user confirms the chosen solution from Phase 2.`

**Incorrect:** No gate; skill barrels forward through expensive operations.
