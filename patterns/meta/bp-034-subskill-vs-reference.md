# BP-034: Sub-skills are for cross-skill reuse only; intra-skill sub-processes stay as reference files

**Source:** Carter's 2026-04-23 clarification during skill-factory v3 planning
**Category:** Composition & pipelines (Meta — authoring discipline)

**Why:** Externalizing a sub-process into its own skill has real costs — new directory, new SKILL.md, new symlink, new fixtures, new compliance surface, new autoresearch workspace. Those costs are only justified when 2+ skills would otherwise reinvent the same machinery. A complex sub-process living inside ONE skill is just another reference file; making it a sub-skill (YAGNI) is pure overhead.

**When applicable:** Any judgment call about whether a process becomes a sub-skill or a reference file. Especially relevant at `skill-spec-validator` (Phase 1 of the driver) when the spec's "Existing skills to reuse" section names any target.

**Enforced by:** `skill-spec-validator` (gap-check: confirms any named `/<skill>` in the reuse section actually exists in the ecosystem); reviewer discipline on PATTERNS.md and SKILLS.md PRs.

**Correct:** `/411-research`, `/411-deck`, `/411-refine` all invoke `/sources-cited` because citation tracking is cross-cutting across the 411 suite. `/411-deck` invokes `/docx` because document generation is ecosystem-wide.

**Incorrect:** A single `/acme-onboarding` skill has a complex "generate new-hire email" sub-process, and the author extracts it into `/acme-generate-email` as a sub-skill — but no other skill uses it. This should have stayed as `references/email-generation.md` inside `/acme-onboarding`.

**Factory architecture note:** The factory's OWN pattern of ~15 sub-skills (skill-frontmatter, skill-phase-designer, etc.) is the exception, not a template client skills should imitate. Authoring patterns ARE cross-cutting — every client skill uses `skill-frontmatter`. Client skills do not have this property with each other, so the factory's output should skew reference-heavy and sub-skill-light.
