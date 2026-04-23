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

## What's live today (Stage 6b)

**Phases 1–4 are operational for the frontmatter slice. Phases 5–6 are architecturally specified but not yet orchestrated** — see `references/phase-spine.md` for the full plan. The slice shipped through Stage 6b:

1. **Phase 1 — Input gate.** Invokes `/skill-spec-validator` on the spec. Hard-exit on gaps.
2. **Phase 2 — Trait classification.** Runs `scripts/trait_predicates.py` to compute the 5 binary trait predicates (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`) against the validated spec. Emits a JSON trait map.
3. **Phase 3 — Context pack materialization.** Runs `scripts/build_context_pack.py` to materialize `phases/01-skill-frontmatter/input.md` from the validated spec + the Phase 2 trait JSON. Per BP-033, sub-skills read ONLY their own input.md — the driver is the sole party that sees the spec and the classifier together.
4. **Phase 4 — Frontmatter sub-skill.** Spawns `skill-frontmatter` as an isolated Agent subtask pointed at the materialized input.md. Returns `output.yaml` (compliant frontmatter) + `output.md` (frontmatter + rationale) + `notes.md` (blockers / observations).

Stage 6b produces a compliant frontmatter YAML for any factory-authored skill hands-off. The other three sub-skills (`skill-phase-designer`, `skill-references-scaffolder`, `skill-compliance-gate`) do not exist yet — the driver stops after Phase 4 and reports.

## Invocation

```
/skill-factory <company> <path-to-client-spec.md>
```

**Example:**
```
/skill-factory acme ~/Claude/specs/acme-onboarding.md
```

## Procedure (what Stage 6b runs)

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

### Step 4 — Phase 4: Spawn skill-frontmatter

Invoke `skill-frontmatter` as an isolated Agent subtask:

- **Pass the exact input.md path** from Step 3.
- **Forbid** the subagent from reading anything else the input.md does not name (the sub-skill's SKILL.md enforces this, but reiterate in the prompt).
- Wait for it to write three files into the phase directory: `output.yaml`, `output.md`, `notes.md`.

Verify the outputs:

```bash
python3 ~/Projects/skill-factory/skill-frontmatter/scripts/frontmatter_lint.py \
    <work>/phases/01-skill-frontmatter/output.yaml
```

- Lint pass (`passed: true`) → continue.
- Lint fail → check `notes.md` for a `BLOCKER:` line. If present, print it to the user and stop (BP-028). If absent but lint still fails, that's a sub-skill protocol violation; report and stop.

### Step 5 — Report and stop (Stage 6b terminus)

Print, in order:
- The pass verdict from Phase 1.
- The trait JSON from Phase 2.
- The applied Universal + Conditional BP list.
- The final `output.yaml` contents from Phase 4.
- The rationale section from `output.md`.
- Any `notes.md` observations.
- The sentence: *"Phases 5–6 not yet orchestrated (deferred to Stage 7+). See `references/phase-spine.md` for the remaining plan."*

No per-client repo is created. No git commits happen. The factory's output so far lives under `<work>/` — the user reviews it and either asks to proceed (when Phase 5/6 ship) or hand-installs the frontmatter.

## Scripts

- **`scripts/trait_predicates.py`** — the 5-predicate classifier. Handles the 4 edge cases from `references/trait-edge-cases.md`. Pure stdlib. Two modes: `spec` (classifying a client-spec.md for authoring) and `skill` (classifying an existing skill directory for dogfood / regression). CLI-runnable directly.
- **`scripts/build_context_pack.py`** — Phase 3 pack materializer. Reads a validated spec + the Phase 2 classifier JSON and emits `input.md` in the exact shape the named sub-skill expects. Currently supports `skill-frontmatter` as the sub-skill target. Pure stdlib. CLI-runnable directly.

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

Expected: **24/24 tests pass** — 10 for `trait_predicates` (every edge case + CLI integration + three spec fixtures) and 14 for `build_context_pack` (section parsing, slug extraction, trait-block rendering, real acme round-trip, negative cases, CLI integration).

## What to do if you're stuck

- **Spec fails Phase 1** → the user fixes the spec per the validator's gap report, then re-runs this skill. Do not attempt to "fix" the spec yourself — spec authorship is the user's responsibility per BP-026.
- **`trait_predicates.py` raises an exception** → write `BLOCKER: trait_predicates.py raised <exception>` to `notes.md` per BP-028 and exit. Do not classify with default/empty values.
- **A trait verdict seems wrong for a given spec** → run `python3 scripts/trait_predicates.py spec <spec-path>` directly to see the `evidence` field for each verdict. Usually the evidence string explains why the predicate fired or didn't.
- **`build_context_pack.py` raises a missing-section error** → the spec is malformed; the validator should have caught it. Re-run `/skill-spec-validator` against the spec path to see which section is missing. Do not try to patch the spec from the driver — BP-026 is the user's responsibility.
- **`skill-frontmatter` writes a `BLOCKER:` line** → surface it to the user verbatim. The common cause is a combined `<company>-<slug>` name exceeding 64 chars (BP-003) — the fix is to shorten the slug in the spec, not in the driver.
- **User asks for a Phase 5–6 capability** → redirect: "Phases 5–6 are Stage 7+ scope. Current build lands at compliant frontmatter YAML; it does not yet produce a full SKILL.md or per-client repo."

## Why Stage 6b stops at Phase 4

BP-029 — build incrementally, no scaffold-and-fill. Three downstream sub-skills (`skill-phase-designer`, `skill-references-scaffolder`, `skill-compliance-gate`) do not exist yet. Writing an orchestrator that invokes non-existent sub-skills would produce untestable code and mask the real work remaining. Stage 7+ will add the next sub-skill (`skill-phase-designer` when `has_phases` fires) and extend this driver with the matching Phase 4 invocation.

The frontmatter slice shipping end-to-end — spec → validator → classifier → pack → subagent → lint-clean YAML — is the correct Stage 6b deliverable. It is the first slice through every phase that a factory-authored skill has in common.

## Patterns enforced

- **BP-023** — Agent-tool composition (Phase 1 invocation of `/skill-spec-validator`, Phase 4 invocation of `skill-frontmatter`)
- **BP-025** — sub-skills are siblings, not nested (skill-frontmatter lives at `~/Projects/skill-factory/skill-frontmatter/`, not under the driver)
- **BP-026** — sole human touchpoint (spec author = only user interaction point; Phases 1–4 run hands-off)
- **BP-027** — input gate before classify (Phase 1 before Phase 2)
- **BP-028** — BLOCKER convention for unrecoverable conditions
- **BP-029** — build incrementally (why Phases 5–6 are deferred, not stubbed)
- **BP-031** — co-locate co-evolving tools (driver + scripts + fixtures in one repo)
- **BP-032** — fixtures at skill root
- **BP-033** — driver-materialized context packs (Phase 3 is the concrete implementation)
- **BP-034** — sub-skills only for cross-skill reuse (enforced at Phase 2 via `invokes_skills` ecosystem check)
