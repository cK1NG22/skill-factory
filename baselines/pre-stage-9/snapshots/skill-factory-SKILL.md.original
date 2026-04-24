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

The Skill Factory's driver. Given a validated `client-spec.md` and a company slug, orchestrates the full pipeline that produces a committed, installed, compliance-passing skill at `~/Projects/<company>-claude-skills/<company>-<slug>/`.

**Sole human touchpoint (BP-026):** the input spec. If the spec passes `/skill-spec-validator`, the downstream pipeline runs hands-off. No mid-pipeline questions, no interactive loops.

## What's live today (Stage 7b)

**Phases 1–4 are operational for frontmatter + phase-design. Phases 5–6 are architecturally specified but not yet orchestrated** — see `references/phase-spine.md` for the full plan. The slice shipped through Stage 7b:

1. **Phase 1 — Input gate.** Invokes `/skill-spec-validator` on the spec. Hard-exit on gaps.
2. **Phase 2 — Trait classification.** Runs `scripts/trait_predicates.py` to compute the 5 binary trait predicates (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`) against the validated spec. Emits a JSON trait map.
3. **Phase 3 — Context pack materialization.** Runs `scripts/build_context_pack.py` to materialize `phases/NN-<sub-skill>/input.md` for every sub-skill that should run on this spec. Per BP-033, sub-skills read ONLY their own input.md — the driver is the sole party that sees the spec and the classifier together.
4. **Phase 4 — Sub-skill composition.** Spawns each qualifying sub-skill as an isolated Agent subtask pointed at its materialized input.md:
   - **4a — Frontmatter (always).** `skill-frontmatter` → `output.yaml` + `output.md` + `notes.md`.
   - **4b — Phase-designer (when `has_phases: true`).** `skill-phase-designer` → `output.md` (draft `## Procedure` section) + `notes.md`.

Stage 7b produces BOTH compliant frontmatter YAML and a lint-passing `## Procedure` section for a phased factory-authored skill, hands-off. The remaining sub-skills (`skill-references-scaffolder`, `skill-compliance-gate`, …) do not exist yet — the driver stops after Phase 4 and reports.

## Invocation

```
/skill-factory <company> <path-to-client-spec.md>
```

**Example:**
```
/skill-factory acme ~/Claude/specs/acme-onboarding.md
```

## Procedure (what Stage 7b runs)

Pick a working directory under `~/Claude/skill-factory/<company>-<slug>/`. All phase outputs land under `<work>/phases/NN-<sub-skill>/`. Treat this directory as the driver's scratch — per-client repo materialization is Phase 6 (not yet implemented).

### Step 1 — Phase 1: Input gate

Invoke `/skill-spec-validator` as an isolated Agent subtask with the spec path. Read the `output.yaml` it returns.

- If `status: pass` → continue to Step 2.
- If `status: gaps` → print the human-readable gap report from `output.md` and exit with the validator's fix instructions. Do NOT proceed. Per BP-027, the input gate is a hard wall.

### Step 2 — Phase 2: Trait classification

Run the classifier and save the JSON to the work dir:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/trait_predicates.py \
    spec <spec-path> > <work>/classifier.json
```

Each trait's `fires` boolean determines which Conditional BPs downstream sub-skills union into their packs:

| Trait fires → | Conditional BPs activated |
|---|---|
| `has_references` | BP-007 |
| `has_phases` | BP-009, BP-010 |
| `has_hitl` | BP-011, BP-012, BP-013, BP-015, BP-016 |
| `is_scheduled` | BP-022 |
| `invokes_skills` | BP-023 (always) + BP-024 (iff also `has_phases`) |

**12 Universal BPs always fire** — see `PATTERNS.md` at repo root for the full list.

### Step 3 — Phase 3: Materialize the skill-frontmatter pack (BP-033)

Run the pack builder:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
    <spec-path> \
    <work>/classifier.json \
    skill-frontmatter \
    <work>/phases/01-skill-frontmatter
```

This writes `<work>/phases/01-skill-frontmatter/input.md` with exactly the sections `skill-frontmatter` expects: Task, Spec excerpt (only the fields frontmatter needs), Classified traits, BPs to enforce (BP-001..BP-005), and Output locations.

The sub-skill will read ONLY this input.md — the driver is the only party that sees the full spec and the classifier together. If the pack builder returns non-zero, it will print the cause to stderr (missing spec section, unsupported sub-skill, bad JSON). Do not retry; surface the error to the user and stop.

### Step 4 — Phase 4a: Spawn skill-frontmatter

Invoke `skill-frontmatter` as an isolated Agent subtask:

- **Pass the exact input.md path** from Step 3.
- **Forbid** the subagent from reading anything else the input.md does not name (the sub-skill's SKILL.md enforces this, but reiterate in the prompt).
- Wait for it to write three files into the phase directory: `output.yaml`, `output.md`, `notes.md`.

Verify the outputs:

```bash
python3 ~/Projects/skill-frontmatter/scripts/frontmatter_lint.py \
    <work>/phases/01-skill-frontmatter/output.yaml
```

- Lint pass (`passed: true`) → continue.
- Lint fail → check `notes.md` for a `BLOCKER:` line. If present, print it to the user and stop (BP-028). If absent but lint still fails, that's a sub-skill protocol violation; report and stop.

### Step 5 — Phase 4b: Spawn skill-phase-designer (when `has_phases: true`)

Read the `has_phases` verdict from `<work>/classifier.json`. If `has_phases.fires` is `false`, skip this step entirely and continue to Step 6 — a non-phased skill needs no Procedure section beyond what `skill-frontmatter` produces.

If `has_phases.fires` is `true`:

**5a. Materialize the phase-designer pack.**

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
    <spec-path> \
    <work>/classifier.json \
    skill-phase-designer \
    <work>/phases/02-skill-phase-designer
```

This writes `<work>/phases/02-skill-phase-designer/input.md` with the sections `skill-phase-designer` needs (Happy-path walkthrough, Inputs, Outputs, Failure modes, Existing skills to reuse — plus HITL-relevant scoping sections when `has_hitl` fires) and the BPs it enforces (BP-010 always; BP-011, BP-012, BP-013, BP-015, BP-016 added when `has_hitl: true`).

**5b. Invoke `skill-phase-designer` as an isolated Agent subtask.**

- **Pass the exact input.md path** from step 5a.
- **Forbid** the subagent from reading anything else the input.md does not name.
- Wait for it to write two files into the phase directory: `output.md` (the draft `## Procedure` section) and `notes.md` (blockers / observations).

**5c. Verify the Procedure with the phase-lint.**

```bash
python3 ~/Projects/skill-phase-designer/scripts/phase_lint.py \
    <work>/phases/02-skill-phase-designer/output.md \
    [--hitl] [--invokes-skills]
```

Pass `--hitl` iff the classifier's `has_hitl.fires` is `true`. Pass `--invokes-skills` iff `invokes_skills.fires` is `true`. Omit either flag when the corresponding trait is `false`.

- Lint pass (`passed: true`) → continue to Step 6.
- Lint fail, `notes.md` has a `BLOCKER:` line → print it to the user and stop (BP-028). The sub-skill already retried internally; a `BLOCKER:` means a second lint failure, so the driver MUST NOT retry further — this is the double-fail hard stop per `skill-phase-designer` Step 10.
- Lint fail, no `BLOCKER:` in `notes.md` → that's a sub-skill protocol violation (the sub-skill must write a BLOCKER on second failure). Print the fail details and stop.

### Step 6 — Report and stop (Stage 7b terminus)

Print, in order:
- The pass verdict from Phase 1.
- The trait JSON from Phase 2.
- The applied Universal + Conditional BP list.
- The final `output.yaml` contents from Phase 4a.
- The rationale section from Phase 4a's `output.md`.
- If Phase 4b ran: the `## Procedure` section from Phase 4b's `output.md`.
- Any `notes.md` observations from Phase 4a and (if it ran) Phase 4b.
- The sentence: *"Phases 5–6 not yet orchestrated (deferred to Stage 8+). See `references/phase-spine.md` for the remaining plan."*

No per-client repo is created. No git commits happen. The factory's output so far lives under `<work>/` — the user reviews it and either asks to proceed (when Phase 5/6 ship) or hand-installs the generated frontmatter + Procedure into a target SKILL.md.

## Scripts

- **`scripts/trait_predicates.py`** — the 5-predicate classifier. Handles the 4 edge cases from `references/trait-edge-cases.md`. Pure stdlib. Two modes: `spec` (classifying a client-spec.md for authoring) and `skill` (classifying an existing skill directory for dogfood / regression). CLI-runnable directly.
- **`scripts/build_context_pack.py`** — Phase 3 pack materializer. Reads a validated spec + the Phase 2 classifier JSON and emits `input.md` in the exact shape the named sub-skill expects. Currently supports `skill-frontmatter` and `skill-phase-designer` as sub-skill targets. Pure stdlib. CLI-runnable directly.

## References

- **`references/phase-spine.md`** — the full 6-phase architecture. Read this to understand the downstream stages.
- **`references/trait-edge-cases.md`** — the 4 classifier gotchas and how `trait_predicates.py` handles each.

## Fixtures

Fixtures live at `fixtures/` (skill root, per BP-032):
- `fixtures/specs/` — three mini client-specs covering different trait combinations.
- `fixtures/skills/` — four mini skill directories exercising edge cases 1–4.
- `fixtures/expected-traits.md` — the classifier oracle.

## Tests

```bash
cd ~/Projects/skill-factory/skill-factory && python3 -m unittest discover tests -v
```

Expected: **35/35 tests pass** — 10 for `trait_predicates` (every edge case + CLI integration + three spec fixtures) and 25 for `build_context_pack` (section parsing, slug extraction, trait-block rendering, real acme round-trip, negative cases, CLI integration, plus skill-phase-designer registration / no-HITL / HITL / CLI tests added in Stage 7b).

## What to do if you're stuck

- **Spec fails Phase 1** → the user fixes the spec per the validator's gap report, then re-runs this skill. Do not attempt to "fix" the spec yourself — spec authorship is the user's responsibility per BP-026.
- **`trait_predicates.py` raises an exception** → write `BLOCKER: trait_predicates.py raised <exception>` to `notes.md` per BP-028 and exit. Do not classify with default/empty values.
- **A trait verdict seems wrong for a given spec** → run `python3 scripts/trait_predicates.py spec <spec-path>` directly to see the `evidence` field for each verdict. Usually the evidence string explains why the predicate fired or didn't.
- **`build_context_pack.py` raises a missing-section error** → the spec is malformed; the validator should have caught it. Re-run `/skill-spec-validator` against the spec path to see which section is missing. Do not try to patch the spec from the driver — BP-026 is the user's responsibility.
- **`skill-frontmatter` writes a `BLOCKER:` line** → surface it to the user verbatim. The common cause is a combined `<company>-<slug>` name exceeding 64 chars (BP-003) — the fix is to shorten the slug in the spec, not in the driver.
- **`skill-phase-designer` writes a `BLOCKER:` line** → surface it verbatim. Common causes: walkthrough has fewer than 3 numbered steps (driver-side trait-classifier bug — `has_phases` should not have fired), or the phase-lint failed twice in a row. Do NOT retry the sub-skill; Phase 4b is a hard stop on BLOCKER per BP-028.
- **User asks for a Phase 5–6 capability** → redirect: "Phases 5–6 are Stage 8+ scope. Current build lands at compliant frontmatter YAML + a lint-passing Procedure section when `has_phases` fires; it does not yet produce a full SKILL.md or per-client repo."

## Why Stage 7b stops at Phase 4

BP-029 — build incrementally, no scaffold-and-fill. The remaining sub-skills (`skill-references-scaffolder`, `skill-compliance-gate`, `skill-cron-observability`, `skill-signed-handoff`) do not exist yet. Writing an orchestrator that invokes non-existent sub-skills would produce untestable code and mask the real work remaining. Stage 8+ will add the next sub-skill (`skill-references-scaffolder` when `has_references` fires) and extend this driver with the matching Phase 4 invocation.

The frontmatter + phase-design slice shipping end-to-end — spec → validator → classifier → two packs → two isolated subagents → lint-clean YAML + lint-clean Procedure — is the correct Stage 7b deliverable. It is the first slice through every phase that a phased factory-authored skill needs.

## Patterns enforced

- **BP-023** — Agent-tool composition (Phase 1 invocation of `/skill-spec-validator`, Phase 4a invocation of `skill-frontmatter`, Phase 4b invocation of `skill-phase-designer`)
- **BP-025** — sub-skills are siblings, not nested (skill-frontmatter + skill-phase-designer live at `~/Projects/skill-factory/skill-*/`, not under the driver)
- **BP-026** — sole human touchpoint (spec author = only user interaction point; Phases 1–4 run hands-off)
- **BP-027** — input gate before classify (Phase 1 before Phase 2)
- **BP-028** — BLOCKER convention for unrecoverable conditions (frontmatter BLOCKER on name overflow, phase-designer BLOCKER on double-lint-fail)
- **BP-029** — build incrementally (why Phases 5–6 are deferred, not stubbed)
- **BP-031** — co-locate co-evolving tools (driver + scripts + fixtures in one repo)
- **BP-032** — fixtures at skill root
- **BP-033** — driver-materialized context packs (Phase 3 is the concrete implementation; each sub-skill reads only its own input.md)
- **BP-034** — sub-skills only for cross-skill reuse (enforced at Phase 2 via `invokes_skills` ecosystem check)
