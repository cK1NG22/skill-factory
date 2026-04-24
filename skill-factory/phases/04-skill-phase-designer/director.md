# Phase 4 — skill-phase-designer (conditional director)

Phase 4 fires when `classifier.json` reports `has_phases.fires: true`.
Otherwise this phase is skipped entirely and the factory proceeds to the
next phase. A non-phased skill needs no `## Procedure` section beyond
what `skill-frontmatter` produces.

## Entry gate

Apply Pattern A (single-trait OR gate) per
`../../references/trait-gating.md`:

```bash
python3 -c "
import json, sys
traits = json.load(open('<work>/classifier.json'))['traits']
sys.exit(0 if traits.get('has_phases', {}).get('fires') else 1)
"
```

Exit 0 → enter Phase 4. Exit 1 → skip to next phase.

See `references/has-phases-gating.md` for the exact edge cases the
classifier handles (alternate phase-section naming, numbered headings)
and why each is treated the way it is.

## Procedure (when the gate passes)

1. **Materialize the phase-designer pack**:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       <spec-path> \
       <work>/classifier.json \
       skill-phase-designer \
       <work>/phases/04-skill-phase-designer
   ```

2. **Spawn `skill-phase-designer`** as an isolated Agent subtask per
   `../../references/spawn-subagent.md`. Pass the exact `input.md` path
   from step 1.

3. **Wait for outputs.** The sub-skill writes two files: `output.md`
   (the draft `## Procedure` section) and `notes.md`.

4. **Verify the Procedure** with the sub-skill's lint, passing the
   trait-dependent flags:

   ```bash
   python3 ~/Projects/skill-factory/skill-phase-designer/scripts/phase_lint.py \
       <work>/phases/04-skill-phase-designer/output.md \
       [--hitl] [--invokes-skills]
   ```

   Pass `--hitl` iff `classifier.json` has `has_hitl.fires: true`.
   Pass `--invokes-skills` iff `invokes_skills.fires: true`. Omit either
   flag when the corresponding trait is `false`.

5. **Interpret the verdict** per BP-028 in
   `../../references/spawn-subagent.md`.

## What this phase does NOT do

- Does NOT assemble the final SKILL.md. The sub-skill produces the
  `## Procedure` section as a standalone draft; the driver hands it to
  Phase 99 for reporting.
- Does NOT re-run the classifier. `classifier.json` from Phase 2 is
  authoritative.
- Does NOT call `skill-phase-designer` for non-phased skills. The gate
  at the top of this director is the sole decision point.

## Cross-reference

- Trait-gating mechanics (Pattern A): `../../references/trait-gating.md`.
- Agent-spawn mechanics: `../../references/spawn-subagent.md`.
- Pack shape (BP-033): `../../references/invocation-contract.md`.
- Predicate edge cases: `references/has-phases-gating.md`.
- Sub-skill's BP-set + HITL additions: `references/phase-designer-invocation.md`.
