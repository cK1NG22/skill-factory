# Phase 5 — skill-references-scaffolder (conditional director)

Phase 5 fires when `classifier.json` reports `has_references.fires: true`.
Otherwise this phase is skipped entirely and the factory proceeds to the
next phase. A skill with no domain-knowledge files needs no `references/`
scaffolding.

## Entry gate

Apply Pattern A (single-trait OR gate) per
`../../references/trait-gating.md`:

```bash
python3 -c "
import json, sys
traits = json.load(open('<work>/classifier.json'))['traits']
sys.exit(0 if traits.get('has_references', {}).get('fires') else 1)
"
```

Exit 0 → enter Phase 5. Exit 1 → skip to next phase.

## Procedure (when the gate passes)

1. **Pre-scaffold the target skill directory.** The sub-skill is a
   verifier — it walks an existing tree. The driver creates that tree
   from the spec's "Reference exemplars" section:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       --prescaffold-references <spec-path> <work>/scaffolded-skill
   ```

   Creates `<work>/scaffolded-skill/references/<name>.md` (one empty
   placeholder per spec entry) plus a stub `SKILL.md` with one canonical
   citation per file. Returns the list of scaffolded names as JSON.

2. **Materialize the references-scaffolder pack** with the target dir:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       <spec-path> <work>/classifier.json skill-references-scaffolder \
       <work>/phases/05-skill-references-scaffolder \
       --target-skill-dir <work>/scaffolded-skill
   ```

3. **Spawn `skill-references-scaffolder`** as an isolated Agent subtask
   per `../../references/spawn-subagent.md`. Pass the exact `input.md`
   path from step 2.

4. **Wait for outputs.** The sub-skill writes two files: `output.md`
   (the scaffolder's plan + lint verdict) and `notes.md`.

5. **Verify the scaffolded tree** with the sub-skill's lint, passing
   the trait-dependent flags:

   ```bash
   python3 ~/Projects/skill-factory/skill-references-scaffolder/scripts/references_lint.py \
       <work>/scaffolded-skill --has-references [--has-phases]
   ```

   Pass `--has-phases` iff `classifier.json` has `has_phases.fires:
   true`. `--has-references` is mandatory — Phase 5 only entered when
   it fires.

6. **Interpret the verdict** per BP-028 in
   `../../references/spawn-subagent.md`.

## What this phase does NOT do

- Does NOT invent reference content. The pre-scaffold creates empty
  placeholders; populating their bodies is a post-factory step the user
  performs (or a future Wave 4 phase).
- Does NOT fire on `has_phases` alone. The scaffolder's BP-009 parallel-
  folders rule needs both `has_references` AND `has_phases` to be
  meaningful — the entry gate is `has_references`, and BP-009 is
  unioned in via `_SUB_SKILL_CONDITIONAL_BPS` when `has_phases` also
  fires.
- Does NOT write into the user's home directory. All scaffolding lands
  under `<work>/scaffolded-skill/`; final placement is Phase 99's job.

## Cross-reference

- Trait-gating mechanics (Pattern A): `../../references/trait-gating.md`.
- Agent-spawn mechanics: `../../references/spawn-subagent.md`.
- Pack shape (BP-033): `../../references/invocation-contract.md`.
- Sub-skill's BP-set + pre-scaffold contract:
  `references/references-scaffolder-invocation.md`.
