# skill-factory (self-bootstrap spec)

Stage 9c self-bootstrap fixture. Describes the **Skill Factory itself**
in client-spec form, so the factory can author itself and the result
can be structurally diffed against the committed `skill-factory/` tree
(Principle D — self-bootstrap is a permanent acceptance criterion).

**Trait expectations:** fires the phases trait (8-step walkthrough) +
the references trait (architectural references library). Does NOT
fire the cadence trait (factory is on-demand), the HITL trait
(factory's gate is the upstream spec validator, not interactive), or
the pipeline trait (deviates from plan v2 — the factory's Phase 1
validator spawn is a mechanical Agent-tool invocation, not a BP-024
pipeline reuse). Expected fire set: **frontmatter + phase-designer +
refs-scaffolder** = 3 sub-skills. The cadence-instrumentation and
handoff-stamping sub-skills stay dormant.

## Company

skill-factory

## Skill slug

skill-factory

## One-line description

The Skill Factory driver — orchestrates the full pipeline that authors a Claude Code skill end-to-end from a validated client spec. Use when "skill factory", "build me a skill", "author a skill from this spec", "generate a skill", "/skill-factory <company> <path-to-client-spec.md>".

## Trigger phrases

- skill factory
- build me a skill
- author a skill from this spec
- generate a skill
- run skill factory

## Inputs

- A `client-spec.md` file path (positional argument 2).
- A company slug (positional argument 1).
- The classifier's working directory at `~/Claude/skill-factory/<company>-<slug>/` (created on demand if absent).

## Outputs

- A `<work>/classifier.json` from Phase 2 with the 5-trait verdicts.
- Per-phase artifacts under `<work>/phases/NN-<sub-skill>/`: frameworks-lint-clean `output.yaml` from Phase 3, `output.md` Procedure section from Phase 4 (when phased), `output.md` scaffolder plan from Phase 5 (when the references trait fires), `instrumentation-snippet.md` from Phase 6 (when the cadence trait fires), `output-signature-template.py` from Phase 7 (when the compound pipeline predicate fires).
- A final report at Phase 99 listing every phase that fired, the artifact paths, and any `notes.md` BLOCKER lines.

## Happy-path walkthrough

1. Pick a working directory at `~/Claude/skill-factory/<company>-<slug>/` and create it if absent. All phase outputs land under `<work>/phases/NN-<sub-skill>/`.
2. Enter Phase 1 (input gate, always fires). Read `phases/01-input-gate/director.md` and execute its procedure. Spawns `/skill-spec-validator` as an isolated Agent subtask. Hard wall per BP-027 — if the validator returns `status: gaps`, surface the gap report verbatim and STOP.
3. Enter Phase 2 (trait classification, always fires). Read `phases/02-trait-classification/director.md` and execute its procedure. Runs `scripts/trait_predicates.py` against the validated spec and writes `<work>/classifier.json` for downstream phases.
4. Enter Phase 3 (frontmatter, always fires). Read `phases/03-skill-frontmatter/director.md` and execute its procedure. Materializes the frontmatter pack via `scripts/build_context_pack.py`, spawns `skill-frontmatter` as an isolated Agent subtask, verifies the produced YAML via `frontmatter_lint.py`.
5. Enter Phase 4 (phase-designer, conditional on `has_phases`). Read `phases/04-skill-phase-designer/director.md` and execute its procedure when `has_phases.fires: true`. Materializes the phase-designer pack, spawns `skill-phase-designer`, verifies the produced Procedure via `phase_lint.py` with the trait-dependent flags.
6. Enter Phase 5 (references-scaffolder, conditional on `has_references`). Read `phases/05-skill-references-scaffolder/director.md` and execute its procedure when `has_references.fires: true`. Pre-scaffolds the target skill directory via `--prescaffold-references`, materializes the refs pack with `--target-skill-dir`, spawns `skill-references-scaffolder`, verifies via `references_lint.py`.
7. Enter Phase 6 (cadence-instrumentation, conditional on its trigger trait). Read the corresponding phase director under `phases/06-*/director.md` and execute its procedure when the trait fires. Materializes the pack, spawns the cadence-instrumentation sub-skill, verifies the produced snippet via the sub-skill's own lint.
8. Enter Phase 7 (cryptographic handoff, conditional on the compound pipeline predicate). Read `phases/07-skill-signed-handoff/director.md` and execute its procedure when the predicate gate exits 0. Materializes the pack, spawns the handoff-stamping sub-skill, verifies the stamped script via the sub-skill's own lint. Then enter Phase 99 (report and stop) — read `phases/99-report/director.md` and print the per-phase summary plus the work directory path.

## Success signals

- Every phase that fires writes its expected artifact set to its phase directory; no phase is left half-complete.
- Each sub-skill's lint returns `passed: true` on the first attempt; on second-attempt failure the sub-skill writes a `BLOCKER:` to `notes.md` per BP-028 and the factory halts cleanly.
- The `<work>/classifier.json` from Phase 2 is byte-stable across re-runs of the same spec — the trait predicates are pure functions over the spec text.

## Failure modes

- **Phase 1 validator returns `status: gaps`** → factory halts at Phase 1, prints the gap report verbatim, exits without entering Phase 2. Per BP-026, the user fixes the spec and re-runs; the factory does NOT attempt to patch the spec itself.
- **`trait_predicates.py` raises an exception** → factory writes `BLOCKER: trait_predicates.py raised <exception>` to `<work>/notes.md` and halts. Does NOT classify with default or empty trait verdicts; the failure is propagated upstream so the spec author can investigate.
- **A sub-skill writes a `BLOCKER:` to its phase `notes.md`** → factory surfaces the BLOCKER verbatim and halts. Does NOT retry the sub-skill — sub-skill BLOCKERs are BP-028 double-fail hard stops, already retried internally.
- **`build_context_pack.py` raises a missing-section error** → spec is malformed in a way the validator should have caught. Factory halts and instructs the user to re-run `/skill-spec-validator`. Does NOT attempt to patch the spec from the driver — BP-026.

## Existing skills to reuse

None.

## Reference exemplars

- `phase-spine.md` — the canonical 8-phase architectural map (Phase 1 through Phase 99). Loaded by the driver to know which phase directors exist and in what order to enter them. Each phase entry summarizes its trigger trait + the BP set it enforces.
- `trait-gating.md` — the three trait-gating patterns (Pattern A inline single-trait, Pattern B compound predicate via `_SUB_SKILL_TRIGGER_PREDICATE`, Pattern C reserved). Loaded by phase directors at gate-entry time to know which mechanism to apply.
- `invocation-contract.md` — the BP-033 `input.md` schema every sub-skill consumes. Loaded by the driver before each Agent spawn so the materialized pack matches what the sub-skill expects.
- `spawn-subagent.md` — the 5-step Agent-tool spawn mechanics shared across every phase that invokes a sub-skill. Loaded by phase directors before invoking any Agent. Encodes BP-028 BLOCKER discipline.
- `trait-edge-cases.md` — the 4 classifier edge cases (sibling .md files, alternate phase-section naming, gstack preamble, paired-family blocklist) and why each is handled the way it is. Loaded only when an unexpected classifier verdict needs investigation.

## Anti-goals

- Does NOT execute or install the produced skill. The factory writes outputs to a working directory; the user manually inspects + installs into `~/.claude/skills/`.
- Does NOT modify the input spec. Spec authorship is the user's responsibility per BP-026; the factory only consumes.
- Does NOT skip phases on quiet failures. Every phase explicitly checks its trigger trait and either enters or skips with a logged reason.
- Does NOT invent sub-skill outputs. If a sub-skill BLOCKERs, the factory halts; it never substitutes default or template content for missing sub-skill output.
