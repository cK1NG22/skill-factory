# BP-025: Sub-skills are siblings (top-level), not nested under driver

**Source:** Phase 1 architecture decision
**Category:** Composition & pipelines (Meta — factory architecture)

**Why:** Sibling sub-skills are independently invocable (`/skill-frontmatter` works alone), show in autocomplete, get their own autoresearch workspace, and have a single source of truth. Nesting under driver-skill loses all four.

**When applicable:** Every sub-skill in `skill-factory`. Factory-internal; not applied to client skills.

**Enforced by:** `skill-references-scaffolder` (refuses to nest sub-skills)

**Correct:** `~/Projects/skill-factory/skill-frontmatter/SKILL.md` symlinked to `~/.claude/skills/skill-frontmatter`.

**Incorrect:** `~/Projects/skill-factory/skill-factory/sub-skills/frontmatter/SKILL.md` (nested, not invocable, not autocompleted).
