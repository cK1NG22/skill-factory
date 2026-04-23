# BP-033: Driver-materialized context packs (driver reads, sub-skills receive paths)

**Source:** 2026-04-23 skill-factory v3 planning session (emerged from 411-suite refinement retrospective)
**Category:** Orchestration & composition (Meta — factory driver discipline)

**Why:** Agent-spawned sub-skills have fresh contexts. Allowing each to independently read shared references (the `patterns/` directory, `SKILLS.md`, manifests, data-contract.md) causes 6–8× token waste per pipeline and risks snapshot drift if a sibling sub-skill modifies a shared ref mid-session. Driver-materialized packs make the driver the single reader and keep every sub-skill's view consistent.

**When applicable:** The `skill-factory` driver, and any future sub-skill that itself spawns nested Agents. Factory-internal; not applied to client skills.

**Enforced by:** `skill-factory` (driver), verified by `skill-compliance` post-hoc (checks that sub-skill SKILL.md files open with a "read only input.md" variant and don't `Read` any files in `patterns/`).

**Correct:** Sub-skill SKILL.md opens with: *"Read ONLY your `phases/NN-<sub-skill>/input.md`. The driver has distilled the specific BP file paths you need into `input.md` — it will list exactly which `patterns/bp-NNN-*.md` files to read (if any). Do NOT open the `patterns/` directory directly."* Driver materializes a sha256-pinned `shared-context/` dir and per-phase `input.md` packs.

**Incorrect:** Sub-skill SKILL.md says "Read `~/Projects/skill-factory/patterns/` and apply all relevant BPs." This forces every sub-skill to re-discover which BPs apply, wastes tokens, and drifts across siblings.

**Cross-reference:** BP-010 ("Apply once, carry forward") is the intra-skill analog of this rule. BP-033 extends the same principle across the Agent boundary to the factory's orchestration layer.
