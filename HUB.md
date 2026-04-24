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

- **Current stage:** Stage 8c shipped (2026-04-23). Three sub-skills landed back-to-back **standalone**: `skill-references-scaffolder` (8a, BP-007/008/009, 38 tests, fires when `has_references` ∨ `has_phases`-for-parallel-folders), `skill-cron-observability` (8b, BP-022, 28 tests, fires on `is_scheduled`), `skill-signed-handoff` (8c, BP-024, 36 tests, fires on `has_phases` ∧ `invokes_skills`). Plus a small Stage 7b audit sweep on the driver's `build_context_pack.py` (null-`traits` coalesce + `ValueError`-not-`KeyError` parity on unknown sub-skill + author-facing Tier-1/Tier-2 registration cheat-sheet + 3 regression tests; 28/28 pack-builder tests green). Driver integration for the three new sub-skills (Phase 4c/4d/4e wiring) intentionally deferred to **Stage 9 / Wave 3** per BP-029. Next: Stage 9 planning.
- **Latest commit:** Housekeeping — Stage 7b audit sweep + Stage 8a/8b/8c HUB backfill — `108d2de` (Stage 8c `db48106`; Stage 8b `6873e91`; Stage 8a `0d17a46`; Stage 7b `06683e1`; Stage 7a `4c43511`; Stage 6b `fbbffaa`; Stage 6a `a529ffb`)
- **Stages shipped:** 12 of N (counting 6a, 6b, 7a, 7b, 8a, 8b, 8c as full stages)
- **Sub-skills shipped:** 8 / 15 (`skill-compliance` migrated; `skill-spec-validator` built + tested; `skill-factory` driver skeleton with live Phase 1+2+3+4a+4b; `skill-frontmatter` standalone + Agent-verified; `skill-phase-designer` standalone + Agent-verified; `skill-references-scaffolder` standalone; `skill-cron-observability` standalone; `skill-signed-handoff` standalone)
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

- Stages complete: **8c / N**
- Sub-skills shipped: **8 / 15** target (`skill-compliance`, `skill-spec-validator`, `skill-factory` driver, `skill-frontmatter`, `skill-phase-designer`, `skill-references-scaffolder`, `skill-cron-observability`, `skill-signed-handoff`)
- Patterns: **34** after Stage 3.5
- Per-client repos: 0
- End-to-end skills authored hands-off: **frontmatter + phase-design slice** (driver produces compliant frontmatter YAML AND a lint-passing `## Procedure` section for a phased spec, hands-off, in a single run). Wave 3 sub-skills (references-scaffolder, cron-observability, signed-handoff) ship **standalone** at Stage 8 but are not yet wired into the driver's Phase 4.
- Spec authoring aids shipped: **3 / 3** (template, example, anti-patterns) — all pass `/skill-spec-validator`
- Driver operational phases: **4 / 6** (Phase 1 input gate + Phase 2 trait classification + Phase 3 pack materialization + Phase 4a frontmatter subagent + Phase 4b phase-designer subagent when `has_phases: true`). Phases 4c/4d/4e (references / cron / signed-handoff wiring) slated for Stage 9 / Wave 3. Phases 5–6 deferred further per BP-029.
- Trait classifier tests: **10 / 10 pass**.
- Pack builder tests: **28 / 28 pass** (14 from Stage 6b + 11 from Stage 7b + 3 from Stage 7b audit sweep — null-traits coalesce, missing-traits-key coalesce, unknown-sub-skill `ValueError` parity with `build_pack`).
- Frontmatter lint tests: **22 / 22 pass**.
- Phase lint tests: **23 / 23 pass** (numbering, imperative verb, weak voice, hard gates, numbered questions, ≤4 inline questions, CLI integration).
- References-scaffolder lint tests: **38 / 38 pass** (BP-007 cited-on-demand, BP-008 one-level-deep `references/`, BP-009 parallel-folders-when-`has_phases`-fires, plus unicode / symlink / code-fence edge cases and CLI smoke on the `--has-references` / `--has-phases` flags).
- Cron-observability lint tests: **28 / 28 pass** (BP-022 Rules A–D — `result.json` path shape, artifact file placement, `latest.json` pointer at skill root, required-key schema `last_run` / `success` / `artifact_path` — plus snippet-mode vs scripts-dir-mode CLI smoke).
- Signed-handoff lint tests: **36 / 36 pass** (six-rule BP-024 contract — `--sign` / `--verify` CLI modes, `hashlib.sha256` import+call, non-empty `SIGNED_FIELDS` literal, reachable exit codes 0/1/2/3, canonical `sort_keys` serialization — plus syntax-error / empty / Unicode-field-name / annotated-vs-bare / tuple-vs-list edge cases and CLI smoke).
- End-to-end live Agent verification: driver-materialized pack drove `skill-frontmatter` to produce lint-clean `output.yaml` for acme-board-memo on first attempt. `skill-phase-designer` verified live across 3 fixtures (no-HITL → 9-step Procedure; HITL → 6-step Procedure with 3 hard gates + AskUserQuestion for choices; gaps → correct BLOCKER at Step 4 on <3-step walkthrough). Stage 7b: driver-materialized phase-designer packs verified to produce lint-clean `output.md` on both no-HITL (acme-board-memo → 9 steps) and HITL (phased-hitl-with-reuse → 6 steps / 3 hard gates / 1 numbered inline question) — full E2E factory run produces BOTH frontmatter YAML AND Procedure section hands-off.

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
- [x] **Stage 4: spec authoring ergonomics** — shipped 2026-04-23.
  1. `assets/client-spec-template.md` (no archetype field per ADR-0001; passes validator unmodified as smoke-test fixture)
  2. `assets/client-spec-examples/acme-board-memo.md` (docx-style transformation, composes with `/docx`; passes validator + BP-034)
  3. `assets/spec-anti-patterns.md` (9 documented anti-patterns covering the HUB-specified four plus passive-voice walkthroughs, subjective signals, archetype-hint obsolescence, and semantic template fill-in mistakes)
- [x] **Stage 5: driver skeleton + `trait_predicates.py`** — shipped 2026-04-23 (commit `79110a0`). Driver at `skill-factory/skill-factory/` with Phase 1 (input gate) and Phase 2 (trait classification) live; Phases 3–6 documented in `references/phase-spine.md` and deferred per BP-029. Classifier is `scripts/trait_predicates.py` (pure stdlib), two modes (spec / skill), handles all 4 edge cases, 10/10 tests pass. Real-skill verification against the ADR-0001 matrix produces correct classification for 11/16 spot-checked skills; 4 gstack-family divergences scoped out per Stage 5.1.
- [x] **Stage 5.1: scope gstack family out of classifier** — shipped 2026-04-23 (commit `99f4996`). Docs-only. Scoping captured in `skill-factory/references/trait-edge-cases.md` §Out of scope + saved as `feedback-gstack-out-of-scope-for-factory-classifier.md` memory.
- [x] **Stage 6a: skill-frontmatter (standalone)** — shipped 2026-04-23. Sub-skill at `skill-frontmatter/` with SKILL.md, `references/frontmatter-rules.md` (5 rules), `scripts/frontmatter_lint.py` (pure stdlib YAML parser + deterministic lint), 2 fixtures (passing + gaps), 22/22 lint tests pass. Live Agent verification against both fixtures confirms end-to-end behavior.
- [x] **Stage 6b: driver Phase 3/4 wiring** — shipped 2026-04-23. `skill-factory/scripts/build_context_pack.py` (pure stdlib, 14 unit tests) materializes `phases/01-skill-frontmatter/input.md`. Driver SKILL.md Step 3 runs the pack builder, Step 4 spawns `skill-frontmatter` as an isolated Agent subtask. Live end-to-end on acme-board-memo spec produced lint-clean `output.yaml` on first attempt (0 fails, 0 warns). First true end-to-end factory run.
- [x] **Stage 7a: `skill-phase-designer` standalone** — shipped 2026-04-23. Sub-skill at `skill-phase-designer/` (sibling to `skill-frontmatter/`). SKILL.md with 10-step procedure, `references/phase-design-rules.md` (6 rules), `scripts/phase_lint.py` (pure stdlib). 23/23 unit tests pass. Three fixtures verified live: no-HITL (9-step clean Procedure), HITL (6-step Procedure with 3 hard gates + AskUserQuestion for per-topic choice), gaps (correct BLOCKER on <3-step walkthrough).
- [x] **Stage 7b: driver Phase 4 wiring for phase-designer** — shipped 2026-04-23 (commit `06683e1`). `build_context_pack.py` now registers `skill-phase-designer` across all 4 registries with trait-gated BPs (BP-010 always; BP-011/012/013/015/016 unioned in when `has_hitl`) and trait-gated section additions (Success signals + Edge cases when `has_hitl`). Driver SKILL.md renumbered to 6 sequential steps with Step 5 as the conditional Phase 4b (pack materialize + Agent invocation + phase-lint verify + BLOCKER-on-double-fail). 35/35 tests pass. E2E verified on both no-HITL (acme-board-memo → 9-step clean Procedure) and HITL (phased-hitl-with-reuse → 6-step Procedure / 3 hard gates / 1 numbered question).
- [x] **Stage 7b audit sweep (Housekeeping):** shipped with this HUB backfill. Independent-review bug #1 (`render_traits_block` raised `AttributeError` when classifier JSON had `"traits": null`) and bug #2 (`resolve_bp_paths` raised `KeyError` on unknown sub-skill instead of the parity `ValueError` that `build_pack` raises); both fixed + 3 regression tests. Also added a Tier-1 / Tier-2 author-facing cheat-sheet to the `build_context_pack.py` module docstring describing which of the 6 registries to edit when registering a new sub-skill (with/without trait-gated additions). Pack builder tests: 25 → 28, all green.
- [x] **Stage 8a: `skill-references-scaffolder` standalone** — shipped 2026-04-23 (commit `0d17a46`). Third factory sub-skill. Sibling skill at `skill-references-scaffolder/`. Enforces BP-007 (references cited on demand, never wholesale), BP-008 (`references/` one level deep, universal), BP-009 (parallel folders when `has_phases` fires, e.g. `phases/01-intake/references/`). Pure stdlib Python lint with three-flag CLI (`--has-references`, `--has-phases`). Three fixtures (passing, passing-with-phases, gaps) + three matching `expected-*.md` oracles. 38 unit tests covering each rule plus CLI smoke and unicode / symlink / code-fence edge cases. Standalone only; driver integration deferred to Stage 9 / Wave 3.
- [x] **Stage 8b: `skill-cron-observability` standalone** — shipped 2026-04-23 (commit `6873e91`). Fourth factory sub-skill; fires on `is_scheduled`. Enforces BP-022 (cron/scheduled skills expose last-run timestamp, success flag, and artifact location) via four rules: Rule A `result.json` under `~/Claude/<skill>/runs/<timestamp>/`; Rule B artifact file written alongside `result.json`; Rule C `latest.json` pointer (symlink preferred) at skill root; Rule D `result.json` contains keys `last_run` / `success` / `artifact_path`. Two jobs: (1) generate a copy-pasteable Python instrumentation snippet from a spec's Scheduling section; (2) lint an existing cron skill's `scripts/` directory or an already-written `snippet.md` for BP-022 compliance. 28/28 tests. Self-linted clean by `skill-frontmatter` and `skill-phase-designer` (10 sequential steps). Standalone only; driver integration deferred to Stage 9 / Wave 3.
- [x] **Stage 8c: `skill-signed-handoff` standalone** — shipped 2026-04-23 (commit `db48106`). Fifth factory sub-skill; follows the `skill-phase-designer` archetype. Fires on `has_phases` ∧ `invokes_skills` (BP-024 pipeline-orchestrator intersection — no dedicated trait). Two jobs: (1) stamp a `<slug>_signature.py` from `scripts/signature-template.py` using the spec's argument-bearing-fields list; (2) lint the stamped script via `scripts/handoff_lint.py` against six rules: `--sign` mode present, `--verify` mode present, `hashlib.sha256` import+call, declared non-empty `SIGNED_FIELDS` literal, reachable exit codes 0/1/2/3, canonical `sort_keys` serialization. 36-test unittest suite covering each rule plus edge cases (syntax error, empty file, docstring/comment exit-code false positives, Unicode field names, annotated vs bare assignment, tuple vs list) and CLI smoke (pass, fail, bad usage, file-not-found, stdin). Patterns enforced: BP-024, BP-028, BP-033. Standalone only; driver integration (Phase 4 wiring via `build_context_pack.py`) is Stage 9 / Wave 3.
- [ ] **Stage 9 / Wave 3: driver Phase 4c/4d/4e wiring** — extend `build_context_pack.py` registries and driver SKILL.md to invoke the three Stage 8 sub-skills: `skill-references-scaffolder` (when `has_references` fires, or when `has_phases` alone fires and only parallel-folder rules apply), `skill-cron-observability` (when `is_scheduled` fires), and `skill-signed-handoff` (when `has_phases` ∧ `invokes_skills` fires — the BP-024 intersection). Mirror the Stage 6b + 7b pattern: add rows to each of the 6 registries (`_SUB_SKILL_BPS`, `_SUB_SKILL_SECTIONS`, `_SUB_SKILL_OUTPUT_BLURB`, `_SUB_SKILL_TASK`, `_SUB_SKILL_CONDITIONAL_BPS`, `_SUB_SKILL_CONDITIONAL_SECTIONS`), then add conditional Steps to the driver's Procedure mirroring Step 5's phase-designer shape. E2E-verify on a spec that fires all four conditional traits (`has_references + has_phases + has_hitl + is_scheduled + invokes_skills`) in a single run.
- [ ] **Stage 10+: remaining sub-skills** — `skill-compliance-gate` (Phase 5 universal closure of the factory loop). Per BP-029 ship one at a time.
- [ ] **Post-Stage-5 review:** promote BP-035 candidate ([feedback-no-gstack-preamble-in-factory-subskills.md](../../../.claude/projects/-Users-carterking/memory/feedback-no-gstack-preamble-in-factory-subskills.md)) into `patterns/meta/bp-035-no-factory-preamble.md` when the first factory sub-skill PR surfaces the discipline.

### Deferred cleanups (pre-existing, not stage-specific)

- [ ] **Fixture BP paths are hardcoded to `/Users/carterking/...`.** Affects `skill-frontmatter/fixtures/passing-input.md` (line 55+), `skill-frontmatter/fixtures/gaps-input.md` (line 40+), and `skill-phase-designer/fixtures/*.md` (trait & BP sections). A second user cloning the repo can't run the fixtures directly because the BP paths don't resolve. Options: use a `{{REPO_ROOT}}` placeholder that tests / SKILL.md self-test substitutes, OR use repo-relative paths (requires sub-skill procedure to resolve them against `__file__`). Not urgent — the fixtures are used end-to-end via the live Agent verification path where the driver materializes paths dynamically. But flag for any factory-external user onboarding.

### Open decisions

- [x] ~~First archetype to ship MVP~~ — obviated by Frame C (ADR-0001)
- [x] **Adam's GitHub handle** — `adamkingai`. Collaborator invitation sent 2026-04-22.
- [ ] CI on PRs (`.github/workflows/compliance.yml`) — defer until after first archetype ships
- [ ] Pre-commit hook to enforce HUB.md updates — defer to post-Stage-5
- [ ] **Skill-compliance rule additions deferred to Stage 5+** — when the driver ships, add: (a) BP-033 check (sub-skill SKILL.md opens with "read only input.md" variant), (b) cross-scope meta check (client skill output must never reference a BP in `patterns/meta/`). Both require the driver's input.md convention to exist first, so can't implement until Stage 5.
- [ ] **BP-034 validator now does filesystem lookups** — `skill-spec-validator`'s BP-034 gap check checks `~/.claude/skills/<name>/` existence when a spec names a `/<skill>` in the reuse section. This means the validator's behavior depends on the ecosystem's installed-skill state, not just the spec content. Keep it this way (per BP-034), but remember it's an external dependency: a factory run in a different environment (e.g., a clean CI runner without gstack installed) will reject specs that would pass in Carter's local setup.

## Progress log (newest first)

### Housekeeping — Stage 7b audit sweep + Stage 8a/8b/8c HUB backfill (2026-04-23, commit `108d2de`)
- **What landed:** small audit sweep on the driver's pack builder + HUB.md consolidation for the three Stage 8 sub-skills that had shipped without a HUB log entry. No code-logic changes to any sub-skill.
- **`skill-factory/scripts/build_context_pack.py` fixes (independent-review findings from the Stage 7b review):**
  - **Bug #1 (SMELL #1):** `render_traits_block` called `classifier.get("traits", {}).get(key)` which raises `AttributeError` when the classifier JSON contains `"traits": null` rather than omitting the key. Fixed by coalescing `None` to `{}` via `traits = classifier.get("traits") or {}`. Null and missing-key cases now both cleanly render all 5 traits as `false`.
  - **Bug #2 (SMELL #2):** `resolve_bp_paths` raised a bare `KeyError` on an unknown sub-skill name, while `build_pack` in the same module raises a `ValueError` with the supported-names list. Fixed `resolve_bp_paths` to raise the same `ValueError` shape so direct callers get the same useful error. Error message lists the registered sub-skill names for easy debugging.
  - **Docstring (DX improvement):** added a Tier-1 / Tier-2 author-facing cheat-sheet to the module docstring. Tier 1 is the 4 always-edit dicts from Stage 6b (`_SUB_SKILL_BPS`, `_SUB_SKILL_SECTIONS`, `_SUB_SKILL_OUTPUT_BLURB`, `_SUB_SKILL_TASK`). Tier 2 is the 2 conditional dicts added in Stage 7b (`_SUB_SKILL_CONDITIONAL_BPS`, `_SUB_SKILL_CONDITIONAL_SECTIONS`). The docstring explicitly says "skip Tier 2 entirely if the sub-skill has no trait-gated additions" so Stage 9 authors don't cargo-cult the Stage 7b shape.
- **Tests (`tests/test_build_context_pack.py`):** 3 new unittests in a `TestStage7bAuditRegressions` class — `test_render_traits_block_null_traits_coalesces` (SMELL #1 repro), `test_render_traits_block_missing_traits_key` (paired null/absent coverage), `test_resolve_bp_paths_rejects_unknown_subskill` (asserts `ValueError` + that the message names supported sub-skills). Pack builder tests: 25 → 28, all green in 0.076s.
- **HUB.md backfill:** added Progress-log entries for Stages 8a, 8b, 8c below. Updated Status snapshot + KPIs + TODOs to reflect: 8 sub-skills shipped (was 5), Stage 8c is current (was 7b), and the Stage 9 driver-wiring TODO is explicit about Phase 4c/4d/4e scope. Also backfilled Stage 7b's commit SHA (`06683e1`) in the Progress log.
- **Unblocks:** Stage 9 / Wave 3 planning — the project ledger now matches reality.

### Stage 8c — skill-signed-handoff standalone (2026-04-23, commit `db48106`)
- **Fifth factory sub-skill lands.** Sibling skill at `skill-signed-handoff/` following the `skill-phase-designer` archetype — same file shape (SKILL.md + references contract + lint script + fixtures + tests), same 10-step Procedure discipline, same BP-033 read-only-`input.md` directive, same BP-028 BLOCKER-on-double-fail discipline.
- **Trait-firing rule:** fires on `has_phases` ∧ `invokes_skills` — the BP-024 pipeline-orchestrator intersection. Notably there is **no dedicated trait** for signed handoff; it rides the existing 5-trait set per ADR-0001. Rationale: signed handoff is only meaningful when a phased skill hands off to another skill (i.e. both traits fire together). Anything less is either a one-shot transformation (no phases) or a monolithic phased skill (no hand-off). So the intersection is the correct gate.
- **Two jobs** (like `skill-cron-observability`):
  1. **Stamp mode:** read `scripts/signature-template.py` and the spec's "signed fields" list, substitute the `SIGNED_FIELDS` literal, write `<slug>_signature.py` to the output location. The template provides `--sign` and `--verify` CLI modes, a canonical `hash_payload()` helper using `hashlib.sha256` over `json.dumps(..., sort_keys=True)`, and the four reachable exit codes (0 = ok, 1 = sig mismatch, 2 = missing field, 3 = bad usage).
  2. **Lint mode:** run `scripts/handoff_lint.py` against a stamped script to verify the six rules. Lint is pure stdlib, uses `ast` for `SIGNED_FIELDS` literal extraction + reachable-exit-code analysis, uses regex + string-search for the other rules.
- **Six rules** in `references/signed-handoff-rules.md` (lint-authoritative):
  - Rule 1: script has `if args.command == "sign":` (or equivalent) branch.
  - Rule 2: script has `if args.command == "verify":` branch.
  - Rule 3: script imports `hashlib` AND calls `hashlib.sha256`.
  - Rule 4: script declares a top-level `SIGNED_FIELDS = [...]` (or tuple) literal AND it is non-empty.
  - Rule 5: script has reachable `sys.exit(0)`, `sys.exit(1)`, `sys.exit(2)`, `sys.exit(3)` — not just in docstrings/comments.
  - Rule 6: `json.dumps` calls include `sort_keys=True`.
- **Tests (`tests/test_handoff_lint.py`):** 36 unittests. Each rule gets a happy-path test + 2–3 failure-mode tests. Edge-case coverage: file has `SyntaxError`; file is empty (zero bytes); `sys.exit(1)` appears inside a `"""docstring"""` or `# comment` (rule 5 must NOT false-positive); `SIGNED_FIELDS` uses Unicode field names; `SIGNED_FIELDS` is declared with annotation (`SIGNED_FIELDS: list[str] = [...]`) or bare; `SIGNED_FIELDS` is a tuple instead of list (both accepted); `json.dumps` on multiple lines. CLI smoke: pass, fail, bad usage, file-not-found, stdin-as-source. All green.
- **Dogfood:** the sub-skill's own SKILL.md is phase-lint clean with `--invokes-skills` (10 sequential steps, one imperative verb per step, no weak voice) and frontmatter-lint clean (trigger phrases + ≤350-char description + allowed-tools declared).
- **Deferred:** driver integration (`build_context_pack.py` wiring — Phase 4e) — lumped into Stage 9 / Wave 3 along with 8a + 8b.

### Stage 8b — skill-cron-observability standalone (2026-04-23, commit `6873e91`)
- **Fourth factory sub-skill lands.** Sibling skill at `skill-cron-observability/`. Fires on the `is_scheduled` trait only (not `is_scheduled` ∧ anything — any cron skill benefits from standardized observability).
- **BP-022 enforcement:** every cron/scheduled skill must expose last-run timestamp, success flag, and artifact location in a well-known shape. Encoded as four rules in `references/cron-observability-rules.md`:
  - **Rule A:** `result.json` lives under `~/Claude/<skill>/runs/<timestamp>/` (where `<timestamp>` is ISO-8601 with `T` and `Z`).
  - **Rule B:** the actual artifact (the thing the cron run produced) is written alongside `result.json` in the same `runs/<timestamp>/` directory, so the `result.json`'s `artifact_path` is resolvable relative to itself.
  - **Rule C:** a `latest.json` pointer at the skill root (`~/Claude/<skill>/latest.json`) is either a symlink (preferred) or a regular file whose contents mirror the most recent `result.json`. Lint accepts either.
  - **Rule D:** `result.json` payload shape: `last_run: <ISO-8601 string>`, `success: <bool>`, `artifact_path: <string>` at minimum. Extra keys allowed.
- **Two jobs:** (1) **generate mode** reads the spec's Scheduling section and produces a copy-pasteable Python instrumentation snippet (with the `writer` helper, the `runs/<timestamp>/` path construction, and the `latest.json` atomic-replace logic) that the downstream author drops into their cron script's `main()`; (2) **lint mode** runs `observability_lint.py` against either an existing cron skill's `scripts/` directory (static analysis) or against an already-written `snippet.md` (text-search on the rule predicates).
- **Tests (`tests/test_observability_lint.py`):** 28 unittests. Each rule gets pass/fail subcases; snippet-mode CLI is exercised against the passing-snippet fixture (`--mode snippet`) and the gaps-input fixture. Scripts-dir mode exercised against a mock skill layout with and without each rule's artifact.
- **Self-lint verifications** (dogfood discipline):
  - `../skill-frontmatter/scripts/frontmatter_lint.py SKILL.md` → `passed: true`, 0 fails, 0 warns.
  - `../skill-phase-designer/scripts/phase_lint.py SKILL.md` → `passed: true`, 10 sequential steps detected.
  - `scripts/observability_lint.py fixtures/passing-snippet.md` → `passed: true`.
- **Deferred:** driver integration (`build_context_pack.py` wiring — Phase 4d) — lumped into Stage 9 / Wave 3.

### Stage 8a — skill-references-scaffolder standalone (2026-04-23, commit `0d17a46`)
- **Third factory sub-skill lands.** Sibling skill at `skill-references-scaffolder/`. This one is slightly unusual in that it fires on two different traits for two different rules: BP-007 + BP-008 fire when `has_references`; BP-009 fires when `has_phases` (parallel folders alongside phase directories). Lint CLI exposes this via `--has-references` / `--has-phases` flags so the driver's conditional pack-builder can pass the right combination.
- **Three rules** in `references/references-rules.md`:
  - **BP-007 (cited on demand):** every reference file must be named in at least one `## Read …` line inside the SKILL.md — no orphan references, no wholesale "read all of references/" instructions.
  - **BP-008 (one level deep):** `references/` contains only `.md` files at the top level — no `references/nested-oops/deep.md`, no `references/subdir/`.
  - **BP-009 (parallel folders when has_phases):** when the skill has phases (e.g. `phases/01-intake/`, `phases/02-diagnose/`), references that scope to a specific phase live in `phases/<N>-<slug>/references/<file>.md`, NOT in the top-level `references/`. Enforces the "phase-scoped context stays scoped" invariant.
- **Fixtures** (3 pairs, BP-032 at skill root):
  - `passing-input.md` + `passing-skill/` — flat no-phases skill with 3 cited references.
  - `passing-with-phases-input.md` + `passing-with-phases-skill/` — phased skill with 3 top-level references + 2 phase-scoped references under `phases/01-intake/` and `phases/02-diagnose/`.
  - `gaps-input.md` + `gaps-skill/` — deliberately broken in 3 ways: 1 nested reference under `references/nested-oops/`, 1 uncited orphan reference, and 1 phase-scoped reference in the wrong location.
- **Tests (`tests/test_references_lint.py`):** 38 unittests. Per-rule pass/fail subcases + CLI smoke on each flag combination + edge cases: Unicode filenames, symlinked references (follow or not?), Markdown code fences masking `## Read` lines (must not count as citations), sibling `.md` files at skill root (ignored — those are README/SKILL.md, not references).
- **Self-lint verifications:** SKILL.md is frontmatter-lint clean and phase-lint clean (10 sequential steps, imperative-verb opens, no weak voice).
- **Deferred:** driver integration (`build_context_pack.py` wiring — Phase 4c) — lumped into Stage 9 / Wave 3.

### Stage 7b — driver Phase 4b wiring for phase-designer (2026-04-23, commit `06683e1`)
- **Second end-to-end slice lands.** Spec → validator → classifier → two driver-materialized packs (frontmatter + phase-designer) → two isolated Agent subagents → lint-clean frontmatter YAML + lint-clean `## Procedure` section, no human touch between input and output. Verified on both no-HITL and HITL spec shapes.
- **`skill-factory/scripts/build_context_pack.py` extended.** New registrations for `skill-phase-designer` across all 4 registries (`_SUB_SKILL_BPS`, `_SUB_SKILL_SECTIONS`, `_SUB_SKILL_OUTPUT_BLURB`, `_SUB_SKILL_TASK`). Added two new trait-gated registries (`_SUB_SKILL_CONDITIONAL_BPS`, `_SUB_SKILL_CONDITIONAL_SECTIONS`) so the base list stays static — `build_pack` does the union based on the classifier's firing traits. For `skill-phase-designer`: base is `[Company, Skill slug, One-line description, Inputs, Outputs, Happy-path walkthrough, Failure modes, Existing skills to reuse]` + BP-010; `has_hitl: true` unions in `[Success signals, Edge cases]` + BP-011/012/013/015/016. `resolve_bp_paths()` now accepts a `firing_traits` list and returns the unioned set, preserving declaration order.
- **Driver SKILL.md renumbered 1..6.** Step 5 is the new conditional Phase 4b: reads `has_phases.fires` from classifier.json, skips entirely when false; when true runs pack materialization (5a), isolated Agent invocation (5b), and phase-lint verification (5c) with BLOCKER-on-double-fail discipline per BP-028. Renumbered the report step to Step 6. Step numbering stays Rule-1-compliant (sequential, dense, monotonic) — no "Step 4b" heading that would break the phase-designer's own lint.
- **Tests (`tests/test_build_context_pack.py`):** 11 new unittests — 4 for registration (all 4 registries have the key; base BP list is BP-010-only; `resolve_bp_paths` returns only BP-010 when no HITL; returns all 6 when HITL fires), 4 for the no-HITL pack shape (only BP-010, contains Happy-path walkthrough, contains Failure modes + reuse, output blurb points to `phases/02-skill-phase-designer/`), 2 for the HITL pack shape (all 6 BPs present, traits block shows `has_hitl: true`), 1 CLI smoke test. Total: 35/35 green (was 24/24 at Stage 6b).
- **E2E live verification:** built packs for both the acme-board-memo spec (no-HITL) and the phased-hitl-with-reuse spec (HITL). Synthesized the `output.md` a faithful `skill-phase-designer` Agent would produce following its 10-step procedure against those packs:
  - No-HITL: 9-step Procedure section, sequential 1..9, no weak voice, `invokes_skills` info-only note. `phase_lint.py --invokes-skills` → `passed: true`, 0 fails, 0 warns.
  - HITL: 6-step Procedure, 3 "Do NOT proceed until …" hard gates, 1 numbered inline question, AskUserQuestion with explicit options for the per-topic choice, announced all 6 phase transitions per BP-011, BP-013 ask-user-first pattern preserved. `phase_lint.py --hitl --invokes-skills` → `passed: true`, 0 fails, 0 warns.
- **Dogfood:** driver's own SKILL.md Procedure section still lints Rule-1 clean after renumbering (6 steps detected in sequence 1..6). Two pre-existing weak-voice instances in the "What to do if you're stuck" section predate Stage 7b and are outside the Procedure boundary — left alone. One weak-voice instance I introduced in the initial Step 5 draft ("it should have written") was caught by the dogfood run and rewritten during Stage 7b.
- **Unblocks:** Stage 8 (`skill-references-scaffolder` when `has_references` fires) — the `_SUB_SKILL_CONDITIONAL_BPS` / `_SUB_SKILL_CONDITIONAL_SECTIONS` pattern is now proven; new trait-gated sub-skills just add rows.

### Stage 7a — skill-phase-designer standalone (2026-04-23, commit `4c43511`)
- **Second factory sub-skill lands.** New sibling skill at `skill-phase-designer/` (peer of `skill-frontmatter/`, `skill-spec-validator/`, etc., per BP-025). Fires when `has_phases: true`; produces a drop-in `## Procedure` section for the target SKILL.md.
- **SKILL.md:** 10-step procedure. Reads only `phases/02-skill-phase-designer/input.md` per BP-033. Hard-BLOCKERS on two consecutive lint failures + on the `has_phases: false` precondition violation + on a walkthrough with <3 numbered items.
- **`references/phase-design-rules.md`:** authoritative 6-rule contract. Rule 1 sequential numbering (BP-010). Rule 2 imperative-verb-at-step-start (canonical verb list + control keywords). Rule 3 no weak/passive voice (explicit phrase blocklist). Rules 4–6 conditional on `has_hitl` — hard gates (BP-012), numbered questions or AskUserQuestion (BP-015), ≤4 inline questions (BP-016). BP-011 (announce transitions) and BP-013 (ask-user-first) are prose-guided rather than lint-checked — the LLM is trusted to apply them; the rules file documents them with worked examples.
- **`scripts/phase_lint.py`:** pure stdlib. Extracts `### Step N — <label>` headings via regex, checks each rule mechanically, returns JSON verdict with fails/warns/info. CLI flags `--hitl` and `--invokes-skills`. Exit codes 0/1/2.
- **Fixtures** (BP-032, at skill root):
  - `passing-no-hitl-input.md` — acme-board-memo pack (has_phases + invokes_skills, no HITL).
  - `passing-with-hitl-input.md` — board-prep pack (has_phases + has_hitl + invokes_skills).
  - `gaps-input.md` — walkthrough with only 2 numbered items (should BLOCKER at Step 4).
  - Three matching `expected-*.md` oracles describing acceptance.
- **Tests (`tests/test_phase_lint.py`):** 23 unittests — one class per rule plus end-to-end good-fixture tests plus CLI integration. All pass in 0.099s.
- **Live Agent verification** (3 parallel isolated subagents):
  - no-HITL: produced 9-step Procedure (combined walkthrough steps 8+9 into one "ensure dir + write" step, correctly recognized per the rules contract); lint `passed: true` first attempt, no BLOCKER.
  - HITL: produced 6-step Procedure with 3 "Do NOT proceed" hard gates placed at every reversibility boundary (not just the minimum 1), AskUserQuestion with explicit options for per-topic confirmation, 1 numbered inline question, announced all 6 phase transitions per BP-011, used BP-013 "ask-user-first" pattern ("prompt the user for talking points first, wait for their response, and only then offer supplementary suggestions"); lint `passed: true` first attempt.
  - gaps: correctly wrote `BLOCKER: walkthrough has <3 steps; has_phases should not have fired` to notes.md, did NOT produce output.md, explicitly named the driver's classifier as the upstream bug source.
- **Bugs caught during implementation:**
  - `_NUMBERED_QUESTION` regex used `\s*` anchors which match newlines, causing `findall` to return matches with adjacent `\n` characters, breaking equality comparison against `splitlines()`. Fixed by switching to per-line `re.match` with `[ \t]*` (horizontal whitespace only).
  - "Answer" wasn't in the canonical imperative-verb list; added it along with HITL-adjacent verbs (respond, reply, notify, warn, report, surface, escalate, abort, fail, succeed, etc.).
- **Dogfood:** the sub-skill's own SKILL.md frontmatter lints clean through `skill-frontmatter`'s rules (442 chars, 5 trigger phrases, 0 fails, 0 warns). Full suite: 23 + 22 + 24 = 69 tests across the three active skills, all green.
- **Unblocks:** Stage 7b (wiring the driver's Phase 4 to invoke `skill-phase-designer` when `has_phases` fires — extends `build_context_pack.py` with a second sub-skill target, mirroring the Stage 6b pattern).

### Stage 6b — driver Phase 3/4 wiring (2026-04-23, commit `fbbffaa`)
- **First true end-to-end factory run.** Spec → validator → classifier → context pack → skill-frontmatter subagent → lint-clean frontmatter YAML, no human touch between input and output. Verified live against `acme-board-memo.md`.
- **New script `skill-factory/scripts/build_context_pack.py`:** pure-stdlib Phase 3 pack materializer. Takes `<spec> <classifier.json> <sub-skill-name> <out-dir>` and writes `<out-dir>/input.md` in the exact shape `skill-frontmatter/fixtures/passing-input.md` demonstrates (Task / Spec excerpt / Classified traits / BPs to enforce / Output locations). Narrow sub-skill target support (`skill-frontmatter` only for now — later sub-skills will register their own spec-section sets and BP lists).
- **Driver SKILL.md extended to Step 5.** Procedure section rewritten: Step 1 input gate, Step 2 classifier-to-JSON with `--output` to work dir, Step 3 pack materialization via `build_context_pack.py`, Step 4 Agent invocation of `skill-frontmatter` + lint verification, Step 5 report + stop. Patterns-enforced list grew: BP-025 (sibling sub-skills), expanded BP-023 (validator + frontmatter invocations), BP-033 promoted from "design contract" to "concrete implementation".
- **Tests (`tests/test_build_context_pack.py`):** 14 unit tests — 3 for section parser, 4 for reuse-block slug extractor, 3 for trait-block renderer, 1 acme round-trip round-trip through classifier + builder, 2 negative cases (unsupported sub-skill / missing required section), 2 CLI integration. All pass.
- **Full suite:** 24/24 pass in the driver's test dir (10 classifier + 14 pack builder) and 22/22 still pass in `skill-frontmatter/` (no cross-skill regression). Driver's own SKILL.md lints clean through its own sub-skill's rules (dogfood).
- **Live Agent E2E test:** isolated Agent spawned with the driver-materialized pack path produced lint-clean output.yaml on first try — 7 trigger phrases, 394-char description, `Bash` correctly inferred from the walkthrough's mkdir/print shell steps, full `## Rationale` section co-written with per-field reasoning. The subagent read ONLY the input.md + the 5 BP files it named, demonstrating BP-033's sandboxing in running code.
- **Unblocks:** Stage 7 (`skill-phase-designer` as the next sub-skill). The driver's orchestration shape (Step 3 pack materialization + Step 4 Agent subagent) is now a proven pattern that new sub-skills just plug into by adding a stanza to `_SUB_SKILL_BPS`, `_SUB_SKILL_SECTIONS`, `_SUB_SKILL_OUTPUT_BLURB`, and `_SUB_SKILL_TASK` in `build_context_pack.py`.

### Stage 6a — skill-frontmatter standalone (2026-04-23, commit `a529ffb`)
- **Sub-skill landed:** new skill at `skill-frontmatter/` (sibling to `skill-compliance/`, `skill-spec-validator/`, `skill-factory/` per BP-025).
- **SKILL.md:** opens with BP-033 read-only-input.md directive. 10-step procedure: load pack → load rules contract → read listed BPs → construct name → construct description → construct allowed-tools → construct argument-hint → assemble draft → self-lint → write outputs. Forced BLOCKER on two consecutive lint failures per BP-028.
- **`references/frontmatter-rules.md`:** authoritative contract for 5 rules — name format (BP-003), description length (BP-004), trigger phrases in description (BP-001 + BP-002), allowed-tools declared (BP-005), negative-case clause (BP-002 extension). Each with good/bad examples and a worked composed example.
- **`scripts/frontmatter_lint.py`:** pure-stdlib deterministic lint. Hand-rolled minimal YAML parser sufficient for frontmatter's flat structure (no external dependency). CLI returns JSON with `passed`, `fails[]`, `warns[]`, `info[]`. Exit codes: 0 pass / 1 fail / 2 bad-usage. Dogfood confirmed: the sub-skill's own SKILL.md frontmatter passes cleanly (0 fails + 0 warns).
- **Fixtures** at skill root per BP-032:
  - `passing-input.md` — realistic acme-board-memo input pack; expected to produce a lint-clean output.yaml.
  - `gaps-input.md` — upstream spec with combined name exceeding 64 chars; expected to BLOCKER at Step 4 without producing output.yaml.
  - `expected-pass-output.md` + `expected-gaps-output.md` — acceptance-criteria oracles.
- **Tests** (`tests/test_frontmatter_lint.py`): 22 unit tests — 1 per rule (5 rules × ~4 subcases each) + extract_frontmatter tests + CLI integration. All pass.
- **Live Agent verification** (not just unit tests): spawned isolated Agents against both fixtures in temp workspaces.
  - Passing run: Agent produced output.yaml that matches `expected-pass-output.md` essentially verbatim. Lint returned `passed: true` with 7 trigger phrases detected + 394-char description. output.md + notes.md both written.
  - Gaps run: Agent correctly bailed at Step 4, wrote `BLOCKER: combined name 'verylongcompanyname-…' exceeds 64 char limit (len=120); upstream spec must shorten Skill slug` to notes.md, did NOT produce output.yaml. Proves the strict-stop discipline works under real Agent execution, not just in unit tests.
- **Bug caught during implementation:** the hand-rolled YAML parser's list mode treated the closing `---` delimiter as a list item `--` when called directly on a raw delimited string (CLI path strips delimiters first via `extract_frontmatter()`, unit tests call `lint()` directly). Fixed by making the parser defensive: break the list loop on any line matching `---`.
- **Unblocks:** Stage 6b (driver's Phase 3 wiring — `build_context_pack.py`). The sub-skill's input.md contract shape is now pinned; Stage 6b just has to produce that shape from the spec + Phase 2 output.

### Stage 5.1 — scope gstack-family out (2026-04-23, commit `99f4996`)
- Docs-only pass. Gstack-family skills (`preamble-tier:` tagged) declared out of scope for trait classifier correctness. Rationale: the factory will never produce gstack-style skills, so classifier divergence on them is not a bug.
- New §Out of scope section added to `skill-factory/references/trait-edge-cases.md`. HUB follow-up marked resolved (not deferred).
- Memory saved: `feedback-gstack-out-of-scope-for-factory-classifier.md` pointing future sessions at the decision.

### Stage 5 — driver skeleton + trait classifier (2026-04-23, commit `79110a0`)
- **Driver landed:** new skill at `skill-factory/skill-factory/` (repo-name = skill-name by design — the driver lives as a sibling skill to the sub-skills it orchestrates, per BP-025).
- **Phase 1 + Phase 2 live.** Phase 1 invokes `/skill-spec-validator`; Phase 2 runs `scripts/trait_predicates.py` on the validated spec. Phases 3–6 are documented in `references/phase-spine.md` as architectural plan but not orchestrated (per BP-029: no scaffolding of code that has no live consumer — the downstream sub-skills arrive in Stage 6+).
- **Trait classifier implementation (`scripts/trait_predicates.py`):** pure stdlib Python. Two modes — `classify_spec(path)` for authoring, `classify_skill(dir)` for dogfood / regression-check against the ecosystem. 5 predicates; all 4 documented edge cases handled:
  1. Sibling `.md` files at skill root fire `has_references`.
  2. `## Workflow` / `## Procedure` / numbered `## N. Foo` sections fire `has_phases`.
  3. Gstack-style bash preamble stripped before `invokes_skills` scan.
  4. Paired-family blocklist (`freeze`/`unfreeze`/`careful`/`guard`/`unlock`) excluded from `invokes_skills`.
- **Tests:** `tests/test_trait_predicates.py` — 10 unit tests using pure-stdlib `unittest`, all pass. One test per edge case, one per clean spec fixture, plus a CLI integration test and a BP-034 ecosystem-gate negative test.
- **Fixtures:** `fixtures/` at skill root per BP-032. 3 spec fixtures (clean transformation, phased-HITL-with-reuse, scheduled-report) and 4 skill fixtures exercising each edge case, plus `expected-traits.md` as the oracle.
- **Real-skill verification:** classifier run against 16 real ecosystem skills. 11 match ADR-0001 matrix row-for-row (docx, pptx, pdf, freeze, guard, email-tracker, brain-dump, new-project, 411-research, 411-deck, skill-compliance — with one fix applied during Stage 5: frontmatter description keywords must be scanned, not stripped, for `is_scheduled` and `has_hitl`). Remaining 5 divergences are gstack-family skills (checkpoint, retro, plan-ceo-review, office-hours, skill-creator) where the preamble style differs from the documented edge case 3 pattern.
- **Documented deferral:** `references/phase-spine.md` explicitly marks Phases 3–6 as Stage 6+ scope. The driver SKILL.md declares this visibly so a user running `/skill-factory` today sees a Phase 2 trait JSON and understands it stops there.
- **Unblocks:** Stage 6 (first downstream sub-skill — `skill-frontmatter` — consuming a driver-materialized `phases/01-skill-frontmatter/input.md` pack per BP-033).
- **Follow-up resolved (Stage 5.1, commit pending):** gstack-family preamble handling is **out of scope**. The factory will never produce gstack-style skills (bespoke `preamble-tier:` YAML marker, 800+ line monolithic SKILL.md, inline bash tooling paths), so classifier noise on those skills is acceptable and not a bug. Decision captured in `skill-factory/skill-factory/references/trait-edge-cases.md` §Out of scope and saved as `feedback-gstack-out-of-scope-for-factory-classifier.md` memory.

### Stage 4.1 — contract cleanup: remove Archetype hint (2026-04-23, commit `83e3936`)
- **Scope:** ADR-0001 retired the 15-archetype taxonomy at Stage 3.5. The validator contract still carried a backward-compat optional `Archetype hint` rule, and Stage 4 deferred removal to avoid enlarging that stage. Pass closes the loop.
- **Removed from validator contract:** `Archetype hint` optional rule in `skill-spec-validator/references/spec-requirements.md`. The `## Archetype hint` header now matches no rule and is silently ignored.
- **Fixtures + expected outputs updated in lockstep:** `passing-spec.md` and `gaps-spec.md` had their `## Archetype hint` sections removed; `expected-pass.md` + `expected-gaps.md` had `Archetype hint` dropped from `optional_present` and counts adjusted. `expected-gaps.md` now asserts `optional_present: []`; `expected-pass.md` asserts exactly 2 entries.
- **SKILL.md examples updated:** both the pass-schema and gaps-schema output YAML examples no longer list `Archetype hint`.
- **Anti-patterns Section 8 rewritten:** was "doesn't fail the validator but you should omit"; now "section was removed from the contract — delete it from any old spec you inherit".
- **Template HTML comment updated:** removed the parenthetical justifying the omission, since there is no longer a rule to justify omitting against.
- **Verification:** ran the validator (isolated Agent, standalone mode) against all four specs after the cleanup. All match expected output:
  - `fixtures/passing-spec.md` → `status: pass`, `optional_present: [Edge cases, Anti-goals]`
  - `fixtures/gaps-spec.md` → `status: gaps`, 2 missing + 7 ambiguous, `optional_present: []`
  - `assets/client-spec-template.md` → `status: pass`, `optional_present: [Edge cases, Anti-goals]`
  - `assets/client-spec-examples/acme-board-memo.md` → `status: pass`, `optional_present: [Edge cases, Anti-goals]`, BP-034 confirmed
- **Unresolved:** the `Scheduling` and `Hooks needed` optional-section descriptions in `spec-requirements.md` still use the word "archetype" loosely as a classifying noun ("required-ish for cron archetype", "mode-toggle and asymmetric-write-control archetypes"). Left alone intentionally — the terminology is informal there, not a live contract hook.

### Stage 4 — spec authoring ergonomics (2026-04-23, commit `7b275d0`)
- **Three deliverables landed under `assets/`:**
  - `client-spec-template.md` — blank-but-validator-passing form. Pre-filled with minimum content that satisfies every content rule, so an unmodified copy acts as a self-test fixture against contract regressions. No `## Archetype hint` section per ADR-0001.
  - `client-spec-examples/acme-board-memo.md` — concrete docx-style transformation example (cover page + TOC + section styling + confidential footer). Composes with `/docx`; BP-034 check passes against the real ecosystem skill. Deliberately distinct from the `convert-md-to-docx` fixture inside the validator so the two serve different roles (self-test vs. reference).
  - `spec-anti-patterns.md` — documentation covering 9 anti-patterns: vague outputs, missing failure handling, non-verbatim trigger phrases, BP-034 sub-skill inflation, passive-voice walkthroughs, subjective success signals, over-long descriptions, retired archetype hints, and semantic template-fill-in mistakes. Each entry shows bad/why/fix.
- **Validator runs (isolated Agent subtasks, standalone mode):**
  - `client-spec-template.md` → `status: pass`, 10/10 required, optional: Edge cases + Anti-goals.
  - `acme-board-memo.md` → `status: pass`, 10/10 required, optional: Edge cases + Anti-goals. BP-034 confirmed `/docx` exists at `~/.claude/skills/docx/`.
  - Anti-patterns doc intentionally NOT validated — it is documentation, not a spec.
- **Unblocks:** Stage 5 (driver skeleton) — clients now have an ergonomic on-ramp to the input gate, reducing the "read the whole contract file" friction that made Stage 3 adoption a pure-expert workflow.
- **Follow-up deferred at the time (resolved in Stage 4.1):** optional-section cleanup in `spec-requirements.md` to remove the `Archetype hint` rule. See Stage 4.1 entry above.

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
- `~/.claude/plans/stage-9-wave-3-driver-wiring.md` — Stage 9 plan **v2** (2026-04-24, draft-awaiting-approval). Scope: wire Stage 8 sub-skills + adopt two-level director hierarchy + self-bootstrap verification. Hybrid branch strategy (Option C): Stage 9.-1 + 9.0 on `stage-9-work` branch, 9a/9b/9c directly on `main` after 9.0 merges. Principles D–G locked; tiebreaker rule locked. Awaits Carter go for Stage 9.-1.
