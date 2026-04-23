---
name: Hub — Skill Factory
description: Project hub — composable factory for authoring Claude Code skills from a client spec. Driver + reusable sub-skills. Per-client output repos. Hands-off vision. Shared between repo (GitHub) and Carter's memory via symlink.
type: project
status: active
originSessionId: 39d17308-dc54-4cfd-aa4c-f202a030961e
---
# Skill Factory — HUB

> Canonical location: `~/Projects/skill-factory/HUB.md`. Symlinked into Carter's memory at `~/.claude/projects/-Users-carterking/memory/hub-skill-factory.md` so edits propagate to both surfaces.
>
> For design rationale see [README.md](README.md), [PATTERNS.md](PATTERNS.md), [SKILLS.md](SKILLS.md), [CONTRIBUTING.md](CONTRIBUTING.md).

## Status snapshot

- **Current stage:** Matrix exercise complete + ADR-0001 landed (2026-04-23). Next: Stage 4 (spec authoring ergonomics).
- **Latest commit:** `88c864c` (ADR-0001)
- **Stages shipped:** 3 of N (N depends on first-archetype exercise; likely 7–9)
- **Sub-skills shipped:** 2 / 15 (`skill-compliance` migrated; `skill-spec-validator` built + tested)
- **Patterns codified:** 34 BPs after Stage 3.5 (was 32; +BP-033 +BP-034)
- **Patterns structure:** 12 Universal / 11 Conditional / 11 Meta — split into `patterns/` directory with per-BP files (Stage 3.5)
- **Traits model:** Frame C rule engine, 5 provisional traits (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`) — PROVISIONAL until BP × real-skill matrix exercise
- **Client skills authored:** 0 (MVP gated on first-archetype decision)

## Repo

[ck22coding/skill-factory](https://github.com/ck22coding/skill-factory) (PRIVATE; Carter + `adamkingai` collaborator)

**Source of truth:** `~/Projects/skill-factory/`. Sub-skills symlinked into `~/.claude/skills/` per-stage.

## Architecture (locked)

| Decision | Choice |
|---|---|
| Composition mechanism | `Agent` tool spawn (isolated subagents) |
| Sub-skill placement | Sibling skills at `~/.claude/skills/skill-<capability>` |
| Infrastructure layer | Thin (no gstack-style preamble tiers / shared bin / templating) |
| Per-client output | Dedicated git repo at `~/Projects/<company>-claude-skills/`, auto-created via `gh` CLI |
| Skill slug naming | `<company>-<skill>` (matches 411 Suite precedent) |
| Install mechanism | Symlinks `~/.claude/skills/...` → `~/Projects/...` |
| Factory's own repo | `ck22coding/skill-factory` private; collaborator-enabled |
| Hands-off goal | Sole human gate = `skill-spec-validator` (Phase 1) |
| Archetype frame (Stage 3.5) | **Frame C — rule engine over 5 provisional traits.** Fixed 15-archetype taxonomy retired. |
| Patterns storage (Stage 3.5) | **Directory of per-BP files** under `patterns/`; `patterns/meta/` physically separates factory-internal BPs. |

## KPIs

_Current state:_

- Stages complete: **3 / N** — Stage 3.5 in-progress
- Sub-skills shipped: **2 / 15** target (~6 expected per first archetype)
- Patterns: **34** after Stage 3.5
- Per-client repos: 0
- End-to-end skills authored hands-off: 0

## TODOs

### In progress (Stage 3.5 — 2026-04-23)

- [x] Break `PATTERNS.md` into `patterns/` directory (24 top-level + 11 meta files + template)
- [x] Add BP-033 (driver context packs) and BP-034 (sub-skills for cross-skill reuse only)
- [x] Rewrite PATTERNS.md as index table
- [ ] Consolidate HUB.md at repo root (this file) + symlink memory
- [ ] Update SKILLS.md with FINDING-emission notes + trait model banner
- [ ] Update CONTRIBUTING.md with new "How to add a pattern" + HUB contribution rule
- [ ] Update `skill-spec-validator` with BP-034 gap check + fixture
- [ ] Save `feedback-subskill-vs-reference.md` memory
- [ ] Commit + push Stage 3.5
- [ ] Verify `/skill-compliance /411-deck` still 13/13

### Next (after matrix + ADR-0001)

- [x] **BP × real-skill matrix exercise** — 20 skills classified; ADR-0001 authored and locks Frame C + 5 traits. Predicate refinements noted for Stage 5 implementation.
- [ ] ~~First archetype decision~~ — **obviated by Frame C.** The factory no longer branches on named archetypes. Stage 4+ proceeds under the rule-engine model.
- [ ] **Stage 4: spec authoring ergonomics** — three deliverables under `skill-factory/assets/`:
  1. `client-spec-template.md` (blank form, NO archetype field per ADR-0001)
  2. `client-spec-examples/<first-example>.md` (recommend a docx-style transformation spec as the first concrete example)
  3. `spec-anti-patterns.md` (common mistakes: vague outputs, missing failure modes, conflicting trigger phrases, single-use sub-skill proposals per BP-034)
  - All three must pass `/skill-spec-validator` cleanly end-to-end.
  - One commit, one stage, stop-and-review after.
- [ ] **Stage 5: driver skeleton + `trait_predicates.py`** — 5-predicate Phase 4 loop. Implementation must handle the 4 classifier edge cases captured in [feedback-trait-classifier-edge-cases.md](../../../.claude/projects/-Users-carterking/memory/feedback-trait-classifier-edge-cases.md): sibling .md as refs, alt phase naming, gstack preamble skip, conservative invokes detection with paired-family toggle exclusion.
- [ ] **Post-Stage-5 review:** promote BP-035 candidate ([feedback-no-gstack-preamble-in-factory-subskills.md](../../../.claude/projects/-Users-carterking/memory/feedback-no-gstack-preamble-in-factory-subskills.md)) into `patterns/meta/bp-035-no-factory-preamble.md` when the first factory sub-skill PR surfaces the discipline.

### Open decisions

- [x] ~~First archetype to ship MVP~~ — obviated by Frame C (ADR-0001)
- [x] **Adam's GitHub handle** — `adamkingai`. Collaborator invitation sent 2026-04-22.
- [ ] CI on PRs (`.github/workflows/compliance.yml`) — defer until after first archetype ships
- [ ] Pre-commit hook to enforce HUB.md updates — defer to post-Stage-5
- [ ] **Skill-compliance rule additions deferred to Stage 5+** — when the driver ships, add: (a) BP-033 check (sub-skill SKILL.md opens with "read only input.md" variant), (b) cross-scope meta check (client skill output must never reference a BP in `patterns/meta/`). Both require the driver's input.md convention to exist first, so can't implement until Stage 5.
- [ ] **BP-034 validator now does filesystem lookups** — `skill-spec-validator`'s BP-034 gap check checks `~/.claude/skills/<name>/` existence when a spec names a `/<skill>` in the reuse section. This means the validator's behavior depends on the ecosystem's installed-skill state, not just the spec content. Keep it this way (per BP-034), but remember it's an external dependency: a factory run in a different environment (e.g., a clean CI runner without gstack installed) will reject specs that would pass in Carter's local setup.

## Progress log (newest first)

### Matrix exercise + ADR-0001 (2026-04-23, commit `88c864c`)
- **20-skill × 5-trait matrix** run against representative skills (docx, pptx, pdf, 411-suite, freeze, guard, email-tracker, skill-creator, autoresearch, skill-compliance, brain-dump, checkpoint, skill-spec-validator, kpi-setter, new-project, retro, plan-ceo-review, office-hours).
- **Findings:** 5 traits are sufficient and necessary — no skill needed a 6th. `invokes_skills` is genuinely rare (~5/20 after false-positive correction), vindicating BP-034. Classifier edge cases surfaced: sibling .md files (pptx/pdf) as de-facto references, alternate phase-section naming (411-research uses "## Workflow"), gstack bash preamble causing false-positive `/gstack` matches, paired-family toggles (freeze/unfreeze).
- **Decision:** Frame C (rule engine over 5 traits) locked. Named-archetype taxonomy retired. Archetype "names" become post-hoc informal labels only.
- **Artifact:** `docs/decisions/ADR-0001-archetype-frame.md` — full rationale, matrix, predicate refinements, alternatives (Frame A/B) rejection reasoning, follow-ups.
- **Unblocks:** Stage 4 (spec authoring ergonomics; template has no archetype field) and Stage 5 (driver's 5-predicate Phase 4 loop).

### Stage 3.5 — structural refinements (2026-04-23, commit `3897071`)
- **PATTERNS.md → directory of per-BP files.** 32 existing BPs split into `patterns/bp-NNN-*.md` (24 files: 23 top-level + template). 9 factory-internal BPs moved to `patterns/meta/`. 2 new BPs added: BP-033 (driver-materialized context packs) and BP-034 (sub-skills for cross-skill reuse only). Total now 34 BPs.
- **Three-bucket classification:** 12 Universal / 11 Conditional / 11 Meta. Traits drive conditionals; universals always fire; meta never applied to client skills.
- **Frame C locked.** Fixed 15-archetype taxonomy replaced by a 5-trait rule engine (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`). Traits PROVISIONAL until matrix exercise.
- **BP-034 gap-check added to `skill-spec-validator`** — validates that any `/<skill>` named in spec's "Existing skills to reuse" section actually exists in the ecosystem.
- **HUB.md consolidated** — this file is canonical at repo root, symlinked from memory.
- **Plan file:** `~/.claude/plans/i-want-to-work-gentle-dolphin.md` (v3, approved 2026-04-23).

### Stage 3 — skill-spec-validator built (2026-04-22, commit `267bc3d`)
`skill-spec-validator` authored end-to-end as the template sub-skill. SKILL.md 151 lines; `references/spec-requirements.md` encoding the 10 required + 6 optional sections of the input quality contract; 4 fixtures covering pass and gaps scenarios. Two isolated Agent subagents independently produced correct outputs on both fixtures (9/9 semantic match on gaps; 10/10 + 3 optional on passing). Compliance 12/13 (1 skip, no scripts/). Post-test polish: tightened issue/fix distinction in SKILL.md, clarified line-number convention, expanded Rule 7 walkthrough. Added BP-032 (fixtures at skill root). Pre-existing fixture location `references/fixtures/` was flagged by compliance as BP-008 nested-reference violation and relocated to top-level `fixtures/`. 570 insertions.

### Stage 2 — skill-compliance migrated (2026-04-22, commit `fba52fc`)
`/skill-compliance` migrated from `~/.claude/skills/skill-compliance/` into `~/Projects/skill-factory/skill-compliance/`. Byte-identical copy verified (md5 match on both files, `diff -rq` clean). Original moved to `~/.claude/skills/skill-compliance.pre-migration-backup/` (reversible). Symlink installed. Post-migration compliance run on `/411-deck` produced identical JSON output to pre-migration baseline (parity confirmed). Backup dir deleted 2026-04-22. 599 insertions.

### Stage 1 — repo + thinking docs (2026-04-22, commit `5643c28`)
Repo created at ck22coding/skill-factory (private). 4 docs pushed: README.md, PATTERNS.md (31 BP entries), SKILLS.md (16 entries), CONTRIBUTING.md. 778 insertions.

### 2026-04-22 Collaborator invited
Adam (GitHub: `adamkingai`) invited to `ck22coding/skill-factory` with write permission. Adam identified from his previously-shared repo `adamkingai/outline-mcp-server`.

### 2026-04-22 Plan approved (v1)
4 rounds of plan iteration; final design in `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md`.

## How to contribute progress entries

After shipping a stage:
1. Add an entry at the top of "Progress log" with stage number, date, commit sha, and 1-paragraph summary.
2. Update the Status snapshot counters.
3. If the stage resolved a TODO, move it from "In progress" to "Done" (or strike it through) and record the resolution in the progress-log entry.
4. Commit together with the stage's code. Recommended commit-message shape: `Stage N: <what shipped> + HUB log`.

## Memory cross-references

- [feedback-incremental-build-not-scaffold-first.md](../../../.claude/projects/-Users-carterking/memory/feedback-incremental-build-not-scaffold-first.md) — anti-pattern that drove Stage cadence
- [feedback-colocate-co-evolving-tools.md](../../../.claude/projects/-Users-carterking/memory/feedback-colocate-co-evolving-tools.md) — why skill-compliance moves into this repo (BP-031)
- [tooling-skill-writing-patterns.md](../../../.claude/projects/-Users-carterking/memory/tooling-skill-writing-patterns.md) — primary source for the Universal/Conditional BPs
- [feedback-skill-knowledge-mapping.md](../../../.claude/projects/-Users-carterking/memory/feedback-skill-knowledge-mapping.md) — knowledge-mapping principle (BP-007/008/009)
- [feedback-kpi-stress-test.md](../../../.claude/projects/-Users-carterking/memory/feedback-kpi-stress-test.md) — KPI rubric (BP-017)
- [411-deck-signed-handoff.md](../../../.claude/projects/-Users-carterking/memory/411-deck-signed-handoff.md) — signed-handoff pattern (BP-024)
- [hub-411-skills.md](../../../.claude/projects/-Users-carterking/memory/hub-411-skills.md) — symlink-into-repo precedent
- [hub-skills-tooling.md](../../../.claude/projects/-Users-carterking/memory/hub-skills-tooling.md) — context: 70-skill ecosystem
- [feedback-subskill-vs-reference.md](../../../.claude/projects/-Users-carterking/memory/feedback-subskill-vs-reference.md) — BP-034 rule (saved Stage 3.5)

## Related work superseded or absorbed

- `hub-skills-tooling.md` TODO D (skill phase persistence) — partially absorbed (resume semantics in driver)
- `hub-skills-tooling.md` TODO E (skill categorization) — fully absorbed; Frame C rule engine replaces any "fixed categorization" need
- `feedback-skill-knowledge-mapping.md` — codified as BP-007/008/009 in patterns/

## Related plans

- `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md` — original approved plan (Stages 1–3 executed against this)
- `~/.claude/plans/i-want-to-work-gentle-dolphin.md` — v3 refinement plan (Stage 3.5 executed against this)
