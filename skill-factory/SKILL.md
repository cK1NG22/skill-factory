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

## What's live today (Stage 5)

**Phases 1 and 2 are operational. Phases 3–6 are architecturally specified but not yet orchestrated** — see `references/phase-spine.md` for the full plan. The narrow slice shipped in Stage 5:

1. **Phase 1 — Input gate.** Invokes `/skill-spec-validator` on the spec. Hard-exit on gaps.
2. **Phase 2 — Trait classification.** Runs `scripts/trait_predicates.py` to compute the 5 binary trait predicates (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`) against the validated spec. Emits a JSON trait map.

Running the driver today produces the Phase 2 JSON trait map and stops. This is the honest incremental ship per BP-029: the classifier proves end-to-end (fixtures + 10 unit tests, all passing), downstream orchestration arrives when its consumer sub-skills exist.

## Invocation

```
/skill-factory <company> <path-to-client-spec.md>
```

**Example:**
```
/skill-factory acme ~/Claude/specs/acme-onboarding.md
```

## Procedure (what Stage 5 runs)

### Step 1 — Phase 1: Input gate

Invoke `/skill-spec-validator` as an isolated Agent subtask with the spec path. Read the `output.yaml` it returns.

- If `status: pass` → continue to Step 2.
- If `status: gaps` → print the human-readable gap report from `output.md` and exit with the validator's fix instructions. Do NOT proceed. Per BP-027, the input gate is a hard wall.

### Step 2 — Phase 2: Trait classification

Run the classifier:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/trait_predicates.py spec <spec-path>
```

Capture the JSON output. Each trait's `fires` boolean determines which Conditional BPs the downstream Phase 4 would union into the build:

| Trait fires → | Conditional BPs activated |
|---|---|
| `has_references` | BP-007 |
| `has_phases` | BP-009, BP-010 |
| `has_hitl` | BP-011, BP-012, BP-013, BP-015, BP-016 |
| `is_scheduled` | BP-022 |
| `invokes_skills` | BP-023 (always) + BP-024 (iff also `has_phases`) |

**12 Universal BPs always fire** — see `PATTERNS.md` at repo root for the full list.

### Step 3 — Report and stop (Stage 5 terminus)

Print:
- The pass verdict from Phase 1.
- The trait JSON from Phase 2.
- The list of Universal BPs + Conditional BPs that would apply to this skill.
- The sentence: *"Phases 3–6 not yet orchestrated (deferred to Stage 6+). See `references/phase-spine.md` for the architectural plan."*

No draft skill is produced. No per-client repo is created. No git commits happen. This is a classify-only run.

## Scripts

- **`scripts/trait_predicates.py`** — the 5-predicate classifier. Handles the 4 edge cases from `references/trait-edge-cases.md`. Pure stdlib. Two modes: `spec` (classifying a client-spec.md for authoring) and `skill` (classifying an existing skill directory for dogfood / regression). CLI-runnable directly.

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
cd ~/Projects/skill-factory/skill-factory && python3 -m unittest tests.test_trait_predicates -v
```

Expected: **10/10 tests pass.** Every edge case has a dedicated test; the CLI has an integration test; spec-mode classification is covered by three fixtures.

## What to do if you're stuck

- **Spec fails Phase 1** → the user fixes the spec per the validator's gap report, then re-runs this skill. Do not attempt to "fix" the spec yourself — spec authorship is the user's responsibility per BP-026.
- **`trait_predicates.py` raises an exception** → write `BLOCKER: trait_predicates.py raised <exception>` to `notes.md` per BP-028 and exit. Do not classify with default/empty values.
- **A trait verdict seems wrong for a given spec** → run `python3 scripts/trait_predicates.py spec <spec-path>` directly to see the `evidence` field for each verdict. Usually the evidence string explains why the predicate fired or didn't.
- **User asks for a Phase 3–6 capability** → redirect: "Phases 3–6 are Stage 6+ scope. Current build only classifies; it does not author."

## Why Stage 5 stops at Phase 2

BP-029 — build incrementally, no scaffold-and-fill. The downstream sub-skills (`skill-frontmatter`, `skill-phase-designer`, `skill-references-scaffolder`, `skill-compliance-gate`) do not exist yet. Writing an orchestrator that invokes non-existent sub-skills would produce untestable code and mask the real work remaining. Stage 6 adds the first downstream sub-skill (`skill-frontmatter`) and extends this driver with the Phase 3 context-pack materialization step that feeds it.

The classifier shipping end-to-end — with fixtures, tests, and real-skill dogfood verification against the ADR-0001 matrix — is the correct Stage 5 deliverable.

## Patterns enforced

- **BP-023** — Agent-tool composition (Phase 1 invocation of `/skill-spec-validator`)
- **BP-026** — sole human touchpoint (spec author = only user interaction point)
- **BP-027** — input gate before classify (Phase 1 before Phase 2)
- **BP-028** — BLOCKER convention for unrecoverable conditions
- **BP-029** — build incrementally (why Phases 3–6 are deferred, not stubbed)
- **BP-031** — co-locate co-evolving tools (driver + scripts + fixtures in one repo)
- **BP-032** — fixtures at skill root
- **BP-033** — driver-materialized context packs (design contract for Phase 3 when Stage 6 implements it)
- **BP-034** — sub-skills only for cross-skill reuse (enforced at Phase 2 via `invokes_skills` ecosystem check)
