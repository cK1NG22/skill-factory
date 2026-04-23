# BP-009: Parallel folders for complex skills (`phases/` + `references/` + `assets/`)

**Source:** `tooling-skill-writing-patterns.md`; confirmed in 411-case (7 phases, 12 references, 3 assets)
**Category:** File structure & references (Conditional — trait: `has_phases`)

**Why:** When a skill has both process instructions (phase files) and knowledge content (theory/framework files), separate them into parallel top-level folders. Two parallel folders at the same depth is fine and does not violate the one-level rule. Nesting `references/` inside `phases/` IS a violation.

**When applicable:** Skills with 3+ phases (trait: `has_phases`).

**Enforced by:** `skill-references-scaffolder`

**Correct:** `skill-name/{SKILL.md, phases/, references/, assets/}` all at one depth.

**Incorrect:** `phases/phase-1/references/foo.md` — nested.
