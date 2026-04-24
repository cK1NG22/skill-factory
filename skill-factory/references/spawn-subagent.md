# Spawning a sub-skill as an isolated Agent subtask

Cross-phase reference shared by every phase director that invokes a sub-skill
(Phase 3 `skill-frontmatter`, Phase 4 `skill-phase-designer`, and the Wave 3
additions: Phase 5 `skill-references-scaffolder`, Phase 6 `skill-cron-observability`,
Phase 7 `skill-signed-handoff`).

This file encodes the five-step mechanics every phase director reuses so the
phase-level directors stay thin and deterministic.

## The five mechanical steps

1. **Materialize the input.md pack** for the target sub-skill via
   `scripts/build_context_pack.py` — see `invocation-contract.md` for the
   pack shape each sub-skill expects.

2. **Spawn the sub-skill as an isolated Agent subtask.**
   - Pass the exact `input.md` path from step 1.
   - Forbid the subagent from reading anything else the `input.md` does not
     name (the sub-skill's own SKILL.md enforces this via BP-033, but the
     driver reiterates it in the Agent prompt as a belt-and-suspenders
     guarantee).

3. **Wait for the sub-skill's output files.** Every sub-skill writes at
   minimum `output.md` (its artifact) and `notes.md` (blockers and
   observations). Some sub-skills also write `output.yaml` (frontmatter)
   or other named files — consult the phase director.

4. **Verify the output with the sub-skill's own lint.** Each sub-skill ships
   a deterministic lint script under `~/.claude/skills/<sub-skill>/scripts/`
   (symlinked to this repo's `<sub-skill>/scripts/`). Run it against the
   sub-skill's primary output file.

5. **Interpret the verdict per BP-028 (BLOCKER-on-double-fail discipline).**
   - Lint `passed: true` → continue to the next phase.
   - Lint fails AND `notes.md` contains a `BLOCKER:` line → print the BLOCKER
     to the user and stop. The sub-skill already retried internally; a
     `BLOCKER:` means a second lint failure, so the driver MUST NOT retry
     further.
   - Lint fails AND `notes.md` contains no `BLOCKER:` line → that's a
     sub-skill protocol violation. Print the lint fail details and stop.

## Why isolation matters

The Agent subtask runs in a fresh context. It cannot see the driver's
conversation, the full spec, or the classifier output — it sees ONLY its
`input.md`. This gives two properties:

- **Determinism:** a sub-skill's output depends only on its `input.md`, so
  two runs with the same `input.md` produce structurally equivalent output.
- **Containment:** if a sub-skill misbehaves, the failure surface is its
  phase directory. Nothing else in the factory run is affected.

## What the driver does NOT do

- Does NOT re-try on first lint failure (the sub-skill retries internally).
- Does NOT write into the sub-skill's phase directory after spawn.
- Does NOT read any sub-skill `references/` content itself — the sub-skill
  reads its own references; the driver only reads the `input.md` contract.

## Cross-reference

- Pack shape per sub-skill: `invocation-contract.md`.
- Trait-gated conditional entry (which phases run at all): `trait-gating.md`.
- BP-028 text: `../../patterns/bp-028-blocker-on-double-fail.md`.
- BP-033 text: `../../patterns/bp-033-driver-materialized-context-packs.md`.
