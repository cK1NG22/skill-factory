# Phase 1 — Input gate (director)

Phase 1 always fires. It is the single hard wall between an unvalidated
client spec and every downstream sub-skill. Per BP-027, a spec that does
not pass the validator does not reach Phase 2.

## Procedure

1. **Invoke `/skill-spec-validator`** as an isolated Agent subtask with the
   spec path. Read the `output.yaml` it returns.
2. **Branch on verdict.**
   - `status: pass` → continue to Phase 2.
   - `status: gaps` → print the human-readable gap report from the
     validator's `output.md` and STOP. Do NOT proceed. The driver does not
     attempt auto-repair.
3. **Record the verdict.** Write the validator's `output.yaml` path into
   the factory run's notes for Phase 99's final report to reference.

See `references/validator-contract.md` for the exact validator schema,
the 10 required spec sections, and the gap-report format.

## Work directory

Pick a working directory under `~/Claude/skill-factory/<company>-<slug>/`.
All phase outputs land under `<work>/phases/NN-<sub-skill>/`. Treat this
directory as the driver's scratch — per-client repo materialization is
Phase 99's Wave 4 scope (not yet implemented).

## What this phase does NOT do

- Does NOT spawn any other sub-skill.
- Does NOT read the classifier (Phase 2 hasn't run yet).
- Does NOT write to the phase directory itself — the `/skill-spec-validator`
  Agent writes its own `output.yaml` / `output.md` / `notes.md` there.

## Cross-reference

- Agent-spawn mechanics shared across all phases: `../../references/spawn-subagent.md`.
- BP-027 text: `../../../patterns/bp-027-input-gate-is-a-hard-wall.md`.
