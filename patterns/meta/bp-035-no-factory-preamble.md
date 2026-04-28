# BP-035: No factory preamble — sub-skill SKILL.md opens directly into procedure

**Source:** 2026-04-23 BP × real-skill matrix exercise (skill-factory v3 planning); promoted from `feedback-no-gstack-preamble-in-factory-subskills.md`
**Category:** Authoring discipline (Meta — factory output shape)

**Why:** Gstack-style bash preambles wire 50+ lines of telemetry, update-checks, proactive config, and timeline logging at the top of SKILL.md before the procedural content begins. That overhead is appropriate for gstack's interactive-CLI purpose, but factory output has no gstack integration — the preamble would be dead weight. Worse, when the driver spawns an `Agent` to run a sub-skill, every byte of SKILL.md eats the Agent's context budget; 50 lines of irrelevant shell directly trades against the budget the sub-skill needs for its actual job. The preamble paths (`~/.claude/skills/gstack/bin/...`) also produce false-positive matches in pattern-based classifiers — the BP × skill matrix flagged `/gstack`, `/codex`, and `/autoplan` as "invoked skills" purely on path-shape, before the gstack scope-out was added.

**When applicable:** Every factory-authored skill — both factory-internal sub-skills (`~/Projects/skill-factory/skill-*/`) and client skills emitted by the materializer. Gstack skills outside the factory are explicitly exempt; this rule only governs factory output.

**Enforced by:** `skill-frontmatter` (Agent prose builds SKILL.md without preamble bash); `skill-compliance` post-hoc (a grep for `~/.claude/skills/gstack/bin/` or `source <(curl` near the top of the file flags violations); ADR-0001 §"Predicate refinements" bullet 4 is the classifier-side complement — gstack-family is scoped out so its preambles can't trigger trait predicates by accident.

**Correct:** SKILL.md body opens with a one-line summary sentence followed directly by the first H2 heading (`## Procedure`, `## Invocation modes`, `## Steps`). If shell setup is unavoidable for a specific sub-skill, extract it to `scripts/<skill>-setup.sh` and reference it with one line in SKILL.md (`Before running, run \`bash scripts/<skill>-setup.sh\` to stage the session directory.`).

**Incorrect:** SKILL.md body opens with `_UPD=...; source <(curl -fsSL ...)` followed by 30+ lines wiring `gstack-update-check`, `gstack-config-get`, `gstack-telemetry-log`, etc. — the procedural content doesn't begin until line 60 and the Agent's context budget is half-spent before it reads its first instruction.

**Cross-reference:** ADR-0001 §"Predicate refinements" bullet 4 (classifier-side scope-out for the gstack family — the upstream half of this rule). BP-034 (sub-skill vs reference — authoring discipline that decides whether the artifact even exists; this BP governs the artifact's shape once it does).
