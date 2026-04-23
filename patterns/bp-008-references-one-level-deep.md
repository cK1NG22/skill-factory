# BP-008: References are one level deep — no nested chains

**Source:** Anthropic skill-creator compliance checklist
**Category:** File structure & references (Universal)

**Why:** `references/foo/bar/baz.md` defeats lazy-loading and makes navigation opaque. Compliance check fails on nesting.

**When applicable:** Every skill (Universal). Note: `patterns/` and `patterns/meta/` in the skill-factory repo root are peer folders outside `references/` scope — BP-008 applies within `references/`, not across the entire repo.

**Enforced by:** `skill-references-scaffolder`, `skill-compliance`

**Correct:** `references/scoping-questions.md`, `references/strategy-overview.md`, `references/anti-patterns.md`

**Incorrect:** `references/phase-1/scoping/questions.md`
