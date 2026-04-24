# Phase 4 — skill-phase-designer (conditional director)

> **Status: PLACEHOLDER (Stage 9.0.1).** This director has not yet been populated.
> Content for this phase currently lives inline in `../../SKILL.md` under
> `### Step 5 — Phase 4b: Spawn skill-phase-designer (when has_phases: true)`.
> Populated during Stage 9.0.3d.

## TODO (Stage 9.0.3d)

Migrate current Step 5 into this director:

- Trait-gated entry (`has_phases.fires: true`) — early-return otherwise.
- Pack materialization + isolated Agent spawn + phase-lint verification.
- BLOCKER discipline per BP-028.
- HITL-trait handling (`--hitl` flag on phase_lint when applicable).
- Pointer to `references/has-phases-gating.md` (phase-scoped, to be created in 9.0.3d).
- Pointer to `references/phase-designer-invocation.md` (phase-scoped, to be created in 9.0.3d).
- Pointers to cross-phase `references/spawn-subagent.md`, `trait-gating.md`,
  `invocation-contract.md`.

Until this is populated, the driver `SKILL.md` remains authoritative for
Phase 4 (phase-designer) execution.
