# BP-023: Sub-skill composition uses the `Agent` tool (not Read+inline)

**Source:** Phase 1 audit of `/skill-creator:189`, `/autoresearch:107`, `/dung`; rejected `context: fork` (zero live examples)
**Category:** Composition & pipelines (Conditional — trait: `invokes_skills`)

**Why:** `Agent` tool spawns subagents with isolated context — driver doesn't bloat with sub-skill intermediate work. Read+inline (used by `/locker`) shares context wastefully and conflates failure modes. Slash-command text in output does NOT trigger dispatch.

**When applicable:** Skills that invoke other skills (trait: `invokes_skills`). See BP-034 — sub-skill invocation is rare in client skills; most use reference files instead.

**Enforced by:** `skill-factory` driver, `skill-signed-handoff`

**Correct:** Driver lists `Agent` in `allowed-tools`; spawns sub-skill with prompt + skill path + workspace dir.

**Incorrect:** Driver `Read`s sub-skill SKILL.md and inlines the instructions.
