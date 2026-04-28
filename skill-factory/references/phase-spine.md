# Phase spine — the 6 phases of the skill-factory driver

**Authoritative architecture for the `skill-factory` driver.** The driver at invocation traverses this spine; each phase has a fixed purpose and a fixed set of sub-skills it may invoke.

Stage 5 implements Phases 1 and 2 only. Phases 3–6 are documented here for architectural clarity but their orchestration is deferred to Stage 6+ when the downstream sub-skills exist.

---

## Phase 1 — Input gate

**Purpose:** Hard-fail on ambiguous or incomplete specs before any downstream work happens.

**Invokes:** `/skill-spec-validator` (existing, Stage 3).

**Live as of:** Stage 3.

**Inputs:** `<company>` slug + path to `client-spec.md`.

**Outputs:** either `status: pass, ready_for_classify: true` (continue) or `status: gaps` with a fix report (exit — user corrects spec and re-runs).

**Blocker convention:** BP-028 — validator writes `BLOCKER:` to `notes.md` on unrecoverable conditions (missing spec file, unreadable contract, malformed markdown).

---

## Phase 2 — Trait classification

**Purpose:** Read the validated spec and derive which Conditional BPs apply.

**Invokes:** `scripts/trait_predicates.py` (Stage 5).

**Live as of:** Stage 5.

**Inputs:** the validated `client-spec.md`.

**Outputs:** a JSON trait map with one verdict per trait:
```json
{
  "mode": "spec",
  "input": "…/client-spec.md",
  "traits": {
    "has_references":  {"fires": false, "evidence": "…"},
    "has_phases":      {"fires": true,  "evidence": "…"},
    "has_hitl":        {"fires": false, "evidence": "…"},
    "is_scheduled":    {"fires": false, "evidence": "…"},
    "invokes_skills":  {"fires": true,  "evidence": "…"}
  }
}
```

**Trait → BP activation (per ADR-0001):**
| Trait | Activates |
|---|---|
| `has_references` | BP-007 |
| `has_phases` | BP-009, BP-010 |
| `has_hitl` | BP-011, BP-012, BP-013, BP-015, BP-016 |
| `is_scheduled` | BP-022 |
| `invokes_skills` | BP-023 (always) + BP-024 (iff also `has_phases`) |

**Universal BPs always fire** (unconditional, 12 total per PATTERNS.md).

---

## Phase 3 — Context-pack materialization (per BP-033)

**Purpose:** For each sub-skill the driver will invoke in Phase 4, write a `phases/NN-<sub-skill>/input.md` that lists the specific BP file paths and the relevant spec excerpt the sub-skill needs. Sub-skills read ONLY their `input.md` — they never open `patterns/` or the spec directly.

**Invokes:** `scripts/build_context_pack.py` (Stage 6+, not yet built).

**Live as of:** DEFERRED to Stage 6 (first consumer: `skill-frontmatter`).

**Design contract:** sub-skill SKILL.md files open with *"Read ONLY your `phases/NN-<sub-skill>/input.md`…"* per BP-033. Reading `patterns/` directly is a compliance violation.

---

## Phase 4 — Sub-skill composition

**Purpose:** Spawn one isolated Agent per sub-skill in topological order. Each Agent reads its `input.md`, produces `output.md` + `output.yaml` + `notes.md`, and returns.

**Invokes (once each sub-skill ships):**
- Universal (every run): `skill-frontmatter` (Stage 6), `skill-kpi-design`, `skill-description-triggers`, `skill-output-contract`, `skill-references-scaffolder` (Stage 7+).
- Conditional on traits: `skill-phase-designer` (has_phases or has_hitl), `skill-cron-observability` (is_scheduled), `skill-signed-handoff` (has_phases ∧ invokes_skills).

**Live as of:** DEFERRED. No downstream sub-skill exists yet beyond `/skill-spec-validator` (Phase 1).

**Composition mechanism:** Agent-tool subagents (BP-023). Each sub-skill runs in a fresh context with only its `input.md` visible. Outputs are serialized to the driver's session workspace.

---

## Phase 5 — Assembly + compliance gate

**Purpose:** Merge all sub-skill outputs into a `draft-skill/` directory with the canonical BP-009 parallel-folder layout. Run `/skill-compliance` against the draft. If it fails, re-invoke the guilty sub-skill with the failure reason (one retry). If it still fails, emit a fix-report and exit.

**Invokes:** `/skill-references-scaffolder` (assembler), `/skill-compliance` (existing, Stage 2).

**Live as of:** DEFERRED to Stage 7+.

---

## Phase 6 — Materialization

**Purpose:** Move the validated draft into the per-client repo at `~/Projects/<company>-claude-skills/<company>-<slug>/`, initialize git if needed, symlink into `~/.claude/skills/`, commit, optionally push.

**Invokes:** `gh` CLI + git. No sub-skill.

**Live as of:** DEFERRED to Stage 7+.

---

## What runs today (Stage 5)

A user running `/skill-factory <company> <spec>` today gets:

1. Phase 1 — spec validation (via `/skill-spec-validator`). Hard-exits on gaps.
2. Phase 2 — trait classification (via `scripts/trait_predicates.py`). Prints JSON trait map.
3. Stops. Phases 3–6 are documented but not orchestrated.

This is an intentionally narrow slice — the classifier proves end-to-end, the downstream orchestration arrives when its consumers (sub-skills) exist. Per BP-029 no scaffold-and-fill.

## Cross-references

- ADR-0001: trait model + predicate definitions
- BP-023: sub-skill composition via Agent tool
- BP-026: sole human touchpoint = the input spec
- BP-027: input gate before classify
- BP-028: BLOCKER convention
- BP-029: build incrementally (why Phases 3–6 are deferred)
- BP-033: driver-materialized context packs (Phase 3 contract)
- BP-034: sub-skills only for cross-skill reuse (Phase 2's `invokes_skills` gate)
- BP-037: thin top-director SKILL.md (the two-level hierarchy this spine documents — top SKILL.md + per-phase `director.md`)
