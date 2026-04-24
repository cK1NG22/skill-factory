# Phase 6 — skill-cron-observability (conditional director)

Phase 6 fires when `classifier.json` reports `is_scheduled.fires:
true`. Otherwise this phase is skipped entirely and the factory
proceeds to the next phase. Non-scheduled skills need no cron
instrumentation.

## Entry gate

Apply Pattern A (single-trait OR gate) per
`../../references/trait-gating.md`:

```bash
python3 -c "
import json, sys
traits = json.load(open('<work>/classifier.json'))['traits']
sys.exit(0 if traits.get('is_scheduled', {}).get('fires') else 1)
"
```

Exit 0 → enter Phase 6. Exit 1 → skip to next phase.

## Procedure (when the gate passes)

1. **Materialize the cron-observability pack** via the pack builder:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
       <spec-path> <work>/classifier.json skill-cron-observability \
       <work>/phases/06-skill-cron-observability
   ```

2. **Spawn `skill-cron-observability`** as an isolated Agent subtask
   per `../../references/spawn-subagent.md`. Pass the exact `input.md`
   path from step 1.

3. **Wait for outputs.** The sub-skill writes three files:
   `instrumentation-snippet.md` (the fenced Python block),
   `output.md` (rationale wrapper), and `notes.md`.

4. **Verify the snippet** with the sub-skill's lint:

   ```bash
   python3 ~/Projects/skill-factory/skill-cron-observability/scripts/observability_lint.py \
       <work>/phases/06-skill-cron-observability/instrumentation-snippet.md
   ```

5. **Interpret the verdict** per BP-028 in
   `../../references/spawn-subagent.md`.

## What this phase does NOT do

- Does NOT install the cron job. The snippet is meant to be pasted
  into the target skill's `scripts/<entrypoint>.py`; scheduling
  registration (cron / launchd / systemd) is a post-factory step.
- Does NOT execute the snippet. The sub-skill emits Python source;
  no `exec()` / `subprocess` from the driver.
- Does NOT run on non-scheduled skills. The entry gate is the sole
  decision point — `is_scheduled.fires` must be true.

## Cross-reference

- Trait-gating mechanics (Pattern A): `../../references/trait-gating.md`.
- Agent-spawn mechanics: `../../references/spawn-subagent.md`.
- Pack shape (BP-033): `../../references/invocation-contract.md`.
- Sub-skill's BP-set + snippet contract:
  `references/cron-observability-invocation.md`.
