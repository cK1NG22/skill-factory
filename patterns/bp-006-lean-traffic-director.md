# BP-006: SKILL.md is a traffic director, 180–220 lines (calibrated by complexity)

**Source:** `tooling-skill-writing-patterns.md` (research-confirmed 2026-03-03)
**Category:** File structure & references (Universal)

**Why:** Lazy-loading benefit lost if SKILL.md balloons. Detail belongs in `references/`. Adding new content should never increase SKILL.md — it goes to references/. The Anthropic 500-line ceiling is the absolute max; 180–220 is the working target for complex skills. Simple single-shot skills can be shorter (100–150 lines) and still compliant.

**When applicable:** Every skill (Universal). Target range scales with skill complexity: single-shot tools land under 180 lines; phased HITL / pipeline-orchestrator / research skills land in the 180–220 ideal range.

**Enforced by:** `skill-references-scaffolder`, `skill-compliance`

**Correct:** SKILL.md has 6 phases × ~25 lines each + frontmatter; detailed rubrics in `references/`.

**Incorrect:** SKILL.md is 600 lines because the author inlined rubrics, examples, and lookup tables.
