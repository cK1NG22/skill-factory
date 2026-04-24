---
name: skill-factory
description: The Skill Factory driver. Authors a Claude Code skill end-to-end from a validated client-spec.md. Orchestrates spec validation, trait classification, context-pack materialization, sub-skill composition, assembly, compliance gate, and per-client repo materialization. Use when "skill factory", "build me a skill", "author a skill from this spec", "generate a skill", "run skill factory", "/skill-factory <company> <spec>". Do NOT use to manually edit skills — that's what direct editing is for. This is for spec-driven authoring.
argument-hint: "<company> <path-to-client-spec.md>"
allowed-tools:
  - Read
  - Bash
  - Agent
---

# skill-factory

The Skill Factory's driver. Given a validated `client-spec.md` and a
company slug, orchestrates the full pipeline that produces a
compliance-passing skill, hands-off. Sole human touchpoint (BP-026): the
input spec. If the spec passes `/skill-spec-validator`, the downstream
pipeline runs without interactive questions.

This SKILL.md is a **thin top director** per Principle E. Every phase's
detailed procedure lives in `phases/<N>-<name>/director.md`. Shared
mechanics live in the cross-phase `references/` files named below. Do
not inline phase logic here.

## Invocation

```
/skill-factory <company> <path-to-client-spec.md>
```

## Procedure

Pick a working directory under `~/Claude/skill-factory/<company>-<slug>/`.
All phase outputs land under `<work>/phases/NN-<sub-skill>/`.

The factory is 5 sequential phases (pre-Wave-3). Each phase has its
own director under `phases/<N>-<name>/director.md`. Read the phase
director when entering that phase — do not inline its logic here.

### Step 1 — Enter Phase 1 (input gate, always fires)

Read `phases/01-input-gate/director.md` and execute its procedure.
Hard wall per BP-027.

### Step 2 — Enter Phase 2 (trait classification, always fires)

Read `phases/02-trait-classification/director.md` and execute its
procedure. Writes `<work>/classifier.json` for downstream phases.

### Step 3 — Enter Phase 3 (frontmatter, always fires)

Read `phases/03-skill-frontmatter/director.md` and execute its
procedure. Produces frontmatter YAML.

### Step 4 — Enter Phase 4 (phase-designer, conditional on has_phases)

Check `has_phases.fires` per `references/trait-gating.md` Pattern A.
When true, read `phases/04-skill-phase-designer/director.md` and
execute its procedure. When false, skip to Step 5.

### Step 5 — Enter Phase 99 (report and stop)

Read `phases/99-report/director.md` and execute its procedure. Print
the per-phase summary and the work directory path.

Phase numbers 05, 06, 07 are reserved for Wave 3 conditional phases
(`skill-references-scaffolder`, `skill-cron-observability`,
`skill-signed-handoff`) landing in Stages 9a and 9b.

## References (cross-phase)

Cross-phase references shared by multiple phase directors. Phase-scoped
references live under `phases/<N>-<name>/references/`.

- Read `references/spawn-subagent.md` for the 5-step Agent-spawn
  mechanics used by every phase that invokes a sub-skill.
- Read `references/trait-gating.md` for Pattern A / Pattern B / Pattern C
  conditional-entry semantics used by every trait-gated phase.
- Read `references/invocation-contract.md` for the BP-033 `input.md`
  schema every sub-skill consumes.
- Read `references/phase-spine.md` for the 6-phase architectural
  overview (Phases 5–6 post-factory scope).
- Read `references/trait-edge-cases.md` for the 4 classifier edge cases
  and why each is handled the way it is.

## Scripts

- **`scripts/trait_predicates.py`** — the 5-predicate classifier. CLI.
- **`scripts/build_context_pack.py`** — Phase 3+4 pack materializer.
  Currently supports `skill-frontmatter` and `skill-phase-designer` as
  sub-skill targets. CLI.

## Fixtures

Fixtures at `fixtures/` (skill root, per BP-032). Three spec fixtures,
four skill fixtures, one classifier oracle.

## Tests

```bash
cd ~/Projects/skill-factory/skill-factory && python3 -m unittest discover tests
```

## What to do if you're stuck

- **Spec fails Phase 1** → the user fixes the spec per the validator's gap report, then re-runs this skill. Do not attempt to "fix" the spec yourself — spec authorship is the user's responsibility per BP-026.
- **`trait_predicates.py` raises an exception** → write `BLOCKER: trait_predicates.py raised <exception>` to `notes.md` per BP-028 and exit. Do not classify with default/empty values.
- **A trait verdict seems wrong for a given spec** → run `python3 scripts/trait_predicates.py spec <spec-path>` directly to see the `evidence` field for each verdict. Usually the evidence string explains why the predicate fired or didn't.
- **`build_context_pack.py` raises a missing-section error** → the spec is malformed; the validator should have caught it. Re-run `/skill-spec-validator` against the spec path to see which section is missing. Do not try to patch the spec from the driver — BP-026 is the user's responsibility.
- **A sub-skill writes a `BLOCKER:` line to `notes.md`** → surface it to the user verbatim per `references/spawn-subagent.md`. Do NOT retry the sub-skill; sub-skill BLOCKERs are BP-028 double-fail hard stops.
- **User asks for a Wave 3 capability that hasn't shipped** → redirect to the current delivery: frontmatter + phase-design hands-off. Wave 3 adds references-scaffolder, cron-observability, and signed-handoff.

## Patterns enforced

- **BP-023** — Agent-tool composition (every phase that invokes a sub-skill)
- **BP-025** — sub-skills are siblings, not nested
- **BP-026** — sole human touchpoint (spec author = only user interaction point)
- **BP-027** — input gate before classify (Phase 1 before Phase 2)
- **BP-028** — BLOCKER convention for unrecoverable conditions
- **BP-029** — build incrementally (why Wave 3 phases are deferred until their sub-skills ship standalone)
- **BP-031** — co-locate co-evolving tools (driver + scripts + fixtures in one repo)
- **BP-032** — fixtures at skill root
- **BP-033** — driver-materialized context packs (the `input.md` contract every sub-skill consumes)
- **BP-034** — sub-skills only for cross-skill reuse (enforced at Phase 2 via `invokes_skills` ecosystem check)
