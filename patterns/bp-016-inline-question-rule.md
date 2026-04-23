# BP-016: Inline question rule — ≤4 questions, each one short sentence

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Workflow & human-in-the-loop (Conditional — trait: `has_hitl`)

**Why:** Question lists in SKILL.md add to context cost. Beyond 4 short questions, move to a `references/scoping-questions.md` and call it from SKILL.md. Keeps the traffic-director lean.

**When applicable:** Skills with user gates mid-flow (trait: `has_hitl`).

**Enforced by:** `skill-phase-designer`, `skill-references-scaffolder`

**Correct:** Inline: 4 single-sentence questions. Or: "Ask the questions in `references/scoping-questions.md`."

**Incorrect:** SKILL.md inlines 12 questions with multi-sentence explanations.
