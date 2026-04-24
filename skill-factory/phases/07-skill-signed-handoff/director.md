# Phase 7 — skill-signed-handoff (AND-conditional director)

Phase 7 fires when `classifier.json` reports BOTH `has_phases.fires:
true` AND `invokes_skills.fires: true` (the BP-024 pipeline-orchestrator
intersection). The trigger is a genuinely compound predicate, not a
single-trait OR-gate — so this director uses the Stage 9b
`build_context_pack.py --should-fire` CLI rather than an inline trait
read. See `references/and-gating.md` for the predicate-registry pattern.

## Entry gate

Apply Pattern B (compound AND-predicate gate) per
`references/and-gating.md`:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
    --should-fire skill-signed-handoff <work>/classifier.json
```

Exit 0 → enter Phase 7. Exit 1 → skip to next phase. Exit 2 → driver
bug; STOP and report.

## Procedure (when the gate passes)

1. **Materialize the signed-handoff pack** via the pack builder:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       <spec-path> <work>/classifier.json skill-signed-handoff \
       <work>/phases/07-skill-signed-handoff
   ```

2. **Spawn `skill-signed-handoff`** as an isolated Agent subtask per
   `../../references/spawn-subagent.md`. Pass the exact `input.md`
   path from step 1.

3. **Wait for outputs.** The sub-skill writes two files:
   `output-signature-template.py` (the stamped Python signature
   script) and `notes.md`.

4. **Verify the stamped script** with the sub-skill's lint:

   ```bash
   python3 ~/Projects/skill-factory/skill-signed-handoff/scripts/handoff_lint.py \
       <work>/phases/07-skill-signed-handoff/output-signature-template.py
   ```

5. **Interpret the verdict** per BP-028 in
   `../../references/spawn-subagent.md`.

## What this phase does NOT do

- Does NOT install the signature script. The stamped file is meant
  to be dropped into the target skill's `scripts/<slug>_signature.py`;
  installation is a post-factory step.
- Does NOT execute the signature script. The sub-skill emits Python
  source; no `exec()` / `subprocess` from the driver.
- Does NOT run when only ONE of `has_phases` / `invokes_skills`
  fires. The AND-gate is the sole decision point — single-trait
  pipelines don't need a signed handoff.

## Cross-reference

- Predicate-registry mechanics (Pattern B): `references/and-gating.md`.
- Trait-gating Patterns A/B/C overview: `../../references/trait-gating.md`.
- Agent-spawn mechanics: `../../references/spawn-subagent.md`.
- Pack shape (BP-033): `../../references/invocation-contract.md`.
- Sub-skill's BP-set + signed-fields contract:
  `references/signed-handoff-invocation.md`.
