# Phase 3 — skill-frontmatter (director)

Phase 3 always fires. Every skill the factory produces needs frontmatter,
so this phase has no conditional gate. Combines what were Steps 3 and 4
of the pre-Stage-9 SKILL.md into a single phase.

## Procedure

1. **Materialize the frontmatter pack** via the pack builder:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       <spec-path> \
       <work>/classifier.json \
       skill-frontmatter \
       <work>/phases/03-skill-frontmatter
   ```

   The pack builder writes `<work>/phases/03-skill-frontmatter/input.md` in
   the shape `skill-frontmatter` expects — see
   `../../references/invocation-contract.md` for the canonical section
   order.

2. **Spawn `skill-frontmatter`** as an isolated Agent subtask per
   `../../references/spawn-subagent.md`. Pass the exact `input.md` path
   from step 1.

3. **Wait for outputs.** The sub-skill writes three files into the phase
   directory: `output.yaml` (the frontmatter), `output.md` (rationale),
   `notes.md` (blockers/observations).

4. **Verify the frontmatter** with the sub-skill's lint:

   ```bash
   python3 ~/Projects/skill-factory/skill-frontmatter/scripts/frontmatter_lint.py \
       <work>/phases/03-skill-frontmatter/output.yaml
   ```

5. **Interpret the verdict** per the BP-028 discipline in
   `../../references/spawn-subagent.md`:
   - `passed: true` → hand the frontmatter to Phase 4.
   - Lint fails AND `notes.md` has a `BLOCKER:` → print the BLOCKER and
     STOP. Do not retry.
   - Lint fails, no `BLOCKER:` → protocol violation; report and STOP.

See `references/frontmatter-invocation.md` for the exact BP-set
(`BP-001..BP-005`) the pack imposes and the `output.yaml` shape the driver
reads.

## What this phase does NOT do

- Does NOT read the `has_phases` trait. Frontmatter fires regardless —
  every skill has frontmatter.
- Does NOT modify the frontmatter itself. If the sub-skill produces
  invalid frontmatter, the driver stops; it does not edit the YAML.
- Does NOT hand-install the frontmatter into the target SKILL.md. That's
  a post-factory step for the user (or a future Wave 4 phase).

## Cross-reference

- Agent-spawn mechanics: `../../references/spawn-subagent.md`.
- `input.md` BP-033 contract: `../../references/invocation-contract.md`.
- Phase-scoped specifics for this sub-skill:
  `references/frontmatter-invocation.md`.
