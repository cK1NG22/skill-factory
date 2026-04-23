# BP-007: Detail in `references/`, loaded on demand

**Source:** Anthropic skill-creator + `tooling-skill-writing-patterns.md`
**Category:** File structure & references (Conditional — trait: `has_references`)

**Why:** Reference files only load into context when SKILL.md explicitly says "Read references/X.md for [purpose]." This keeps context lean — detail available, not always loaded.

**When applicable:** Any skill with frameworks, lookup tables, or examples > ~10 lines (trait: `has_references`).

**Enforced by:** `skill-references-scaffolder`, `skill-compliance`

**Correct:** SKILL.md says `Read references/strategy-overview.md to load the per-phase theory map.`

**Incorrect:** SKILL.md inlines a 200-line table of frameworks.
