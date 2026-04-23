# BP-031: Co-locate tools that co-evolve in the same repo

**Source:** `feedback-colocate-co-evolving-tools.md`; Carter's Phase 4 round 2 requirement to migrate `/skill-compliance` into the factory repo
**Category:** Authoring discipline (Meta — repo organization)

**Why:** When a tool and the rules it enforces evolve together, separate repos create stale-rubric problems. New best-practice → new compliance rule → new sub-skill behavior should ship as one PR, not three coordinated ones.

**When applicable:** Any meta-tool (factory) and the rule artifacts it operates on. Factory-internal organizational principle.

**Enforced by:** Repo organization decisions; reviewer discipline.

**Correct:** `skill-compliance` lives in `~/Projects/skill-factory/skill-compliance/` alongside `patterns/`.

**Incorrect:** `skill-compliance` in a separate repo while patterns evolve here.
