# SKILLS — sub-skill catalog

Every skill in this repo has an entry below. Format: purpose, inputs, outputs, enforced patterns, when invoked, standalone usability, status. New sub-skill = PR adding entry here BEFORE authoring the SKILL.md (BP-030).

**Status legend:**
- 🟢 **Live** — implemented, tested, in production use
- 🟡 **Migrated** — existed elsewhere, moved into this repo (no behavior change)
- 🔵 **Planned (Stage N)** — not yet implemented; will land in stage N
- ⚪ **Deferred** — not in current roadmap, may be added later

---

## Orchestration model (Stage 3.5 — Frame C rule engine)

The factory does NOT branch on named archetypes. Instead, the driver at Phase 4 evaluates **5 trait predicates** against the validated spec and unions sub-skills from whichever traits fire. Patterns are split across three buckets:

- **12 Universal BPs** — every skill gets the sub-skills that enforce these, unconditionally.
- **11 Conditional BPs** — each tied to ONE of the 5 traits below. Triggered only if the trait fires.
- **11 Meta BPs** (in `patterns/meta/`) — factory-internal; never applied to client skills.

**The 5 traits (PROVISIONAL until BP × real-skill matrix exercise produces ADR-0001):**

| Trait | Fires when spec… | Brings in |
|---|---|---|
| `has_references` | has framework/lookup content >10 lines | BP-007 enforcement (skill-references-scaffolder) |
| `has_phases` | happy-path walkthrough has ≥3 distinct steps | BP-009, BP-010 (skill-phase-designer) |
| `has_hitl` | declares user gates/questions mid-flow | BP-011, BP-012, BP-013, BP-015, BP-016 (skill-phase-designer) |
| `is_scheduled` | has a scheduling section | BP-022 (skill-cron-observability) |
| `invokes_skills` | names existing `/<skill>` in reuse section (BP-034 gates) | BP-023 (always) + BP-024 (iff also `has_phases`) |

**Optimization runs are CLI flags, NOT traits:** `--polish-autoresearch`, `--polish-triggers`, `--polish-benchmark`. The factory produces `kpi.md`, `trigger-evals.md`, and `test-prompts.md` artifacts universally (cheap); running any optimization loop against them is a separate decision.

**Sub-skill discipline (BP-033):** Every sub-skill reads ONLY its `phases/NN-<name>/input.md`. The driver lists specific BP file paths in `input.md`. Sub-skills never open `patterns/` directly.

**FINDING emission:** Any sub-skill that observes a pattern not currently in `patterns/` may emit a `FINDING: <proposed BP>` line in its `notes.md`. The driver collects these post-pipeline into `findings/session-findings.md` for PR-based promotion.

---

## skill-factory (the driver)

**Purpose:** Orchestrate the end-to-end authoring of a Claude Code skill from a `client-spec.md`. Under Frame C (ADR-0001) the driver routes: spec → `/skill-spec-validator` → trait classification via `trait_predicates.py` → (Phase 3+ context-pack materialization → sub-skill composition → assembler → compliance gate → per-client repo materialization, deferred to Stage 6+).
**Inputs:** `<company>` slug + path to `client-spec.md`
**Outputs (today, Stage 6b):** Phase 1 pass verdict + Phase 2 JSON trait map + Phase 3 materialized `input.md` pack + Phase 4 compliant frontmatter `output.yaml` (with rationale + notes). Driver terminates after Phase 4 — the SKILL.md body (procedure, references, assembly, per-client repo) is still Stage 7+ work.
**Outputs (future, Stage 7+):** New skill landed at `~/Projects/<company>-claude-skills/<company>-<slug>/`, symlinked into `~/.claude/skills/<company>-<slug>`, committed + pushed.
**Enforces patterns:** BP-023 (Agent-tool composition — validator + frontmatter), BP-025 (sibling sub-skills), BP-026 (sole human touchpoint), BP-027 (input gate before classify), BP-028 (BLOCKER convention), BP-029 (build incrementally), BP-031 (co-locate co-evolving), BP-032 (fixtures at skill root), BP-033 (driver-materialized context packs — concrete implementation), BP-034 (sub-skills only for cross-skill reuse)
**When invoked:** User-initiated. `/skill-factory <company> <spec-path>`.
**Standalone usable:** Yes — this IS the entry point.
**Status:** 🟢 Live (Stage 6b shipped 2026-04-23) — Phases 1–4 operational. 24/24 unit tests pass (10 classifier + 14 pack builder). First true end-to-end factory run verified live against acme-board-memo: driver-materialized pack drove `skill-frontmatter` subagent to produce lint-clean `output.yaml` on first attempt (0 fails, 0 warns). Phases 5–6 deferred to Stage 7+ per BP-029.

---

## skill-spec-validator

**Purpose:** Gate the pipeline on input quality. Either green-lights the spec (all required sections present, unambiguous) or returns surgical gap-fills with line-numbers and required-field hints. The single human touchpoint per the hands-off vision.
**Inputs:** Path to `client-spec.md`
**Outputs:** `STATUS: pass` (with `sections_found`, `optional_present`, `ready_for_classify: true`) OR `STATUS: gaps` (with `missing_required[]`, `ambiguous_required[]`, fix instructions, `ready_for_classify: false`)
**Enforces patterns:** BP-026 (sole human touchpoint), BP-027 (input gate before classify), BP-028 (BLOCKER convention as fail-mode), BP-032 (fixtures at skill root)
**When invoked:** Driver Phase 1 (always, first). Also independently invocable for ad-hoc spec checking.
**Standalone usable:** Yes — `/skill-spec-validator path/to/spec.md` returns same output.
**Status:** 🟢 Live (Stage 3 complete 2026-04-22). 12/13 compliance (1 skip for scripts/). Verified end-to-end against both fixtures via isolated Agent subagents — passing-spec → STATUS: pass with 10/10 required + 3 optional; gaps-spec → STATUS: gaps with 2 missing + 7 ambiguous (9/9 semantic match against expected-gaps.md). Template for all future sub-skills.

---

## skill-frontmatter

**Purpose:** Generate compliant skill frontmatter — `name`, `description` (with trigger phrases), `allowed-tools`, optional `argument-hint` — from the validated spec + classified archetype. Includes self-lint against frontmatter rules before writing output.
**Inputs:** `phases/01-skill-frontmatter/input.md` (distilled spec excerpt + archetype) — reads `spec.md` and `archetype.json` from session workspace.
**Outputs:** `output.yaml` (raw frontmatter block, parseable) + `output.md` (frontmatter + rationale) + `notes.md`.
**Enforces patterns:** BP-001 (trigger phrases), BP-002 (pushy description), BP-003 (name limits), BP-004 (description ≤1024), BP-005 (allowed-tools declared)
**When invoked:** Driver Phase 4, first sub-skill. Stage 6a ships it standalone; Stage 6b wires the driver's Phase 3 to materialize its input.md pack.
**Standalone usable:** Yes — `/skill-frontmatter <phases-dir-or-input-md-path>`. Reads `input.md`, produces `output.yaml` + `output.md` + `notes.md` in the same directory.
**Status:** 🟢 Live + driver-integrated (Stage 6a shipped 2026-04-23 as `a529ffb`; Stage 6b wired the driver 2026-04-23). 22/22 lint tests pass. Stage 6b's `build_context_pack.py` materializes this sub-skill's `input.md` from the driver's Phase 2 output; first end-to-end factory run against acme-board-memo produced lint-clean `output.yaml` on first try (0 fails, 0 warns, 7 trigger phrases, 394-char description).

---

## skill-description-triggers

**Purpose:** Optimize a skill's description for reliable triggering. Generates 20 trigger eval queries (8–10 should-trigger + 8–10 near-miss should-not-trigger), runs them against the description, iterates with extended thinking up to 5 times, picks best by held-out test score. Wraps Anthropic `/skill-creator`'s `run_loop.py`.
**Inputs:** Skill path + initial description
**Outputs:** `best_description` (string) + iteration report HTML + scores
**Enforces patterns:** BP-001 (trigger phrases), BP-002 (pushy description), BP-019 (eval test cases)
**When invoked:** Optional polish phase (driver Phase 6, with `--polish` flag) for any archetype that wants triggering optimization.
**Standalone usable:** Yes — `/skill-description-triggers <skill-path>`.
**Status:** ⚪ Deferred (wraps existing Anthropic infrastructure; build when first archetype needs polish)

---

## skill-output-contract

**Purpose:** Author the output structure FIRST as a rendering contract — before any process steps. Forces inline rendering of all required sections, prevents "executive-summary-only" outputs. The lesson from 411-refine's 0.572 → 0.827 jump.
**Inputs:** Spec's "Outputs" section + archetype
**Outputs:** A `## Required output structure` block to insert into the target SKILL.md
**Enforces patterns:** BP-020 (write output contract first), BP-021 (output home convention)
**When invoked:** Driver Phase 4, in transformation, single-shot tool, review/audit, variant-generation, trend/longitudinal archetypes.
**Standalone usable:** Yes — `/skill-output-contract <spec-section>`.
**Status:** 🔵 Planned (Stage 7+, depending on first-archetype choice)

---

## skill-phase-designer

**Purpose:** Break a multi-step process from the spec into named phases with announce/gate/ask-first/rationale-with-because templates. Numbers questions per phase. Decides checkpoint density based on reversibility.
**Inputs:** Spec's "Happy-path walkthrough" + archetype
**Outputs:** `phases/` folder with one `<NN>-<phase-name>.md` file per phase, each with announce text, ask-first questions, rationale clauses, and hard gates.
**Enforces patterns:** BP-010 (apply once carry forward), BP-011 (announce transitions), BP-012 (hard gates), BP-013 (ask user first), BP-014 (rationale with because), BP-015 (numbered questions), BP-016 (inline question rule)
**When invoked:** Driver Phase 4, in phased HITL, taste-gated HITL, pipeline-orchestrator, multi-model-reasoning, research/synthesis, meta/optimizer, guidance/consult.
**Standalone usable:** Yes.
**Status:** 🔵 Planned (Stage 7+)

---

## skill-knowledge-mapper

**Purpose:** For every process step in a target skill, declare what the model must KNOW at that step and which reference file holds that knowledge. Enforces over-documentation discipline. Produces a step→reference-file map.
**Inputs:** Phases output from `skill-phase-designer`
**Outputs:** `references/` folder skeleton with one `<topic>.md` per knowledge area, each step in `phases/` cross-linked to its references.
**Enforces patterns:** BP-007 (detail in references), BP-008 (one level deep), BP-009 (parallel folders), BP-010 (apply once carry forward)
**When invoked:** Driver Phase 4, in phased HITL, pipeline-orchestrator, research/synthesis, multi-model-reasoning, guidance/consult.
**Standalone usable:** Yes.
**Status:** 🔵 Planned (Stage 7+)

---

## skill-kpi-design

**Purpose:** Define phase + holistic KPIs for a target skill via `/kpi-setter`, then auto-stress-test each KPI against Observable / Specific / Not gameable / Not compound rubric. Refuses to finalize until all KPIs pass stress-test.
**Inputs:** Phases output + spec's "Success signals"
**Outputs:** `kpi.md` consumable by `/autoresearch`
**Enforces patterns:** BP-017 (Observable/Specific/Not gameable/Not compound), BP-018 (KPI before autoresearch)
**When invoked:** Driver Phase 4, in any archetype that wants `/autoresearch` refinement (phased HITL, pipeline-orchestrator, research/synthesis, meta/optimizer).
**Standalone usable:** Yes — wraps `/kpi-setter` with the stress-test layer.
**Status:** 🔵 Planned (Stage 7+ if first archetype is phased-HITL or pipeline-orchestrator; later otherwise)

---

## skill-signed-handoff

**Purpose:** When a target skill is a multi-skill pipeline, author the sha256-signed handoff contract between upstream and downstream phases (411-deck pattern). Generates the signing script, verification script, and exit codes.
**Inputs:** Pipeline manifest declaring upstream/downstream phases + which fields to sign
**Outputs:** `scripts/handoff_signature.py` with `--sign`/`--verify` modes; downstream Phase 1 boilerplate that verifies before proceeding.
**Enforces patterns:** BP-024 (signed handoffs)
**When invoked:** Driver Phase 4, only in pipeline-orchestrator and multi-model-reasoning archetypes.
**Standalone usable:** Yes — `/skill-signed-handoff <pipeline-spec>`.
**Status:** ⚪ Deferred (until first pipeline-orchestrator archetype ships)

---

## skill-hook-wiring

**Purpose:** Author the `hooks.PreToolUse` / `settings.json` entries for mode-toggle and asymmetric-write-control archetypes. Generates the hook script (e.g., `bin/check-freeze.sh`) and the frontmatter `hooks:` block.
**Inputs:** Spec's "Hooks needed" section + archetype
**Outputs:** `bin/<hook-name>.sh` + frontmatter `hooks:` block to inject
**Enforces patterns:** BP-005 (allowed-tools declared)
**When invoked:** Driver Phase 4, only in mode-toggle and asymmetric-write-control archetypes.
**Standalone usable:** Yes.
**Status:** ⚪ Deferred (until first mode-toggle archetype ships)

---

## skill-script-bundler

**Purpose:** Detect when a target skill's process would benefit from a bundled script (e.g., file conversion, format parsing) vs ad-hoc inline code. If 3+ test runs would produce the same helper, emit it once into `scripts/` and reference it from SKILL.md. Reduces per-invocation token cost.
**Inputs:** Spec's "Inputs" + "Outputs" + "Happy-path walkthrough"
**Outputs:** `scripts/<utility>.py` + reference in SKILL.md to use it.
**Enforces patterns:** BP-021 (output home — script outputs go to ~/Claude/)
**When invoked:** Driver Phase 4, in transformation and variant-generation archetypes.
**Standalone usable:** Yes.
**Status:** 🔵 Planned (Stage 7+ if transformation is first archetype)

---

## skill-cron-observability

**Purpose:** For scheduled/cron and trend/longitudinal archetypes, add the last-run / success / artifact-location logging required by BP-022. Generates the run-log script and the inspection helper (`/<skill>-status`).
**Inputs:** Spec's "Scheduling" section + archetype
**Outputs:** Run logger to `~/Claude/<skill>/runs/<timestamp>/result.json` + `latest.json` symlink + cron plist (if archetype is scheduled/cron).
**Enforces patterns:** BP-021 (output home), BP-022 (cron observability)
**When invoked:** Driver Phase 4, only in scheduled/cron and trend/longitudinal archetypes.
**Standalone usable:** Yes.
**Status:** ⚪ Deferred (until first cron archetype ships)

---

## skill-references-scaffolder

**Purpose:** The assembler. Merges all phase outputs from the session workspace into `draft-skill/`. Creates the parallel-folder structure (`SKILL.md` + `phases/` + `references/` + `assets/`) per BP-009, ensures references are one level deep per BP-008, validates SKILL.md is in 180–220 line target per BP-006.
**Inputs:** Session workspace `phases/` directory (all sub-skill outputs)
**Outputs:** `draft-skill/` populated and ready for compliance gate
**Enforces patterns:** BP-006 (180–220 line SKILL.md), BP-007 (detail in references), BP-008 (one level deep), BP-009 (parallel folders), BP-025 (sub-skills are siblings — refuses to nest)
**When invoked:** Driver Phase 5, before compliance gate. Always runs (universal post-amble).
**Standalone usable:** Yes — `/skill-references-scaffolder <session-workspace>`.
**Status:** 🔵 Planned (Stage 7+)

---

## skill-compliance

**Purpose:** Standalone 13-check audit (6 required + 7 best-practice) against any skill directory. Pure-stdlib Python. Migrated into this repo because the rubric co-evolves with the patterns the factory enforces (BP-031).
**Inputs:** Path to a skill directory (e.g., `~/.claude/skills/411-deck/` or `~/Projects/skill-factory/skill-spec-validator/`)
**Outputs:** Pass/fail report listing each check + reason for any failures.
**Enforces patterns:** BP-001, BP-003, BP-004, BP-005, BP-006, BP-007, BP-008, BP-021 (and growing — patterns added to PATTERNS.md should add corresponding checks here)
**When invoked:** Standalone for ad-hoc audit; wrapped by `skill-compliance-gate` for in-pipeline use.
**Standalone usable:** Yes — `/skill-compliance <path>`.
**Status:** 🟢 Live + 🟡 Migrated (Stage 2 complete 2026-04-22). Source now at `~/Projects/skill-factory/skill-compliance/`; `~/.claude/skills/skill-compliance` is a symlink into the repo. Parity verified: 13/13 pass on `/411-deck` via both the pre-migration dir and the post-migration symlink (identical output diff).

---

## skill-compliance-gate

**Purpose:** Wraps `skill-compliance` for in-pipeline use within the driver's Phase 5. Auto-fix loop: on failure, re-invoke the relevant sub-skill with the failure as context (one retry); if still failing, exit with a fix-report.
**Inputs:** `draft-skill/` from `skill-references-scaffolder`
**Outputs:** `compliance-report.md` (pass) or `fix-report.md` (fail) + flag indicating whether to proceed to materialization.
**Enforces patterns:** All patterns enforced by `skill-compliance` (delegated)
**When invoked:** Driver Phase 5, after assembly. Universal post-amble.
**Standalone usable:** No — designed for in-pipeline use. Use `/skill-compliance` directly for standalone audits.
**Status:** 🔵 Planned (Stage 7+)

---

## skill-eval-loop

**Purpose:** Optional polish for archetypes that benefit from quantitative testing. Wraps Anthropic `/skill-creator`'s eval loop: spawns parallel with-skill + baseline subagents on test prompts, grades, aggregates into benchmark.json, opens viewer for human review, iterates.
**Inputs:** Path to a draft skill + 3–5 test prompts (auto-generated from spec's success signals if absent)
**Outputs:** `eval-report.md` + benchmark scores per iteration; updated draft skill incorporating iteration feedback.
**Enforces patterns:** BP-019 (eval test cases)
**When invoked:** Optional driver Phase 6 (with `--polish` flag) for any archetype.
**Standalone usable:** Yes — `/skill-eval-loop <skill-path>`.
**Status:** ⚪ Deferred (wraps existing Anthropic machinery; build when polish is needed)

---

## skill-autoresearch-gate

**Purpose:** Optional refinement loop. Wraps `/autoresearch` to drive a draft skill toward higher KPI scores via iterative prompt edits. Refuses to run without a stress-tested `kpi.md` (BP-018).
**Inputs:** Path to a draft skill + its `kpi.md`
**Outputs:** Refined SKILL.md + `runs/results.tsv` showing per-iteration scores.
**Enforces patterns:** BP-017 (KPI rubric), BP-018 (KPI before autoresearch)
**When invoked:** Optional driver Phase 6 (with `--polish` flag) for archetypes that produce a `kpi.md` (phased HITL, pipeline-orchestrator, research/synthesis, meta/optimizer).
**Standalone usable:** Yes — `/skill-autoresearch-gate <skill-path>`.
**Status:** ⚪ Deferred

---

## Sub-skill build dependency graph (Stage 3.5 — Frame C aligned)

```
Universal (always fire, built first):
    skill-compliance        [migrated Stage 2]  ← enforces universals + conditionals
    skill-spec-validator    [Stage 3]           ← Phase 1 gate, BP-034 check
    skill-frontmatter       [Stage 6 planned]   ← BP-001..005 enforcement
    skill-references-scaffolder [Stage 7+]      ← BP-006, BP-008, BP-020 enforcement
    skill-output-contract   [Stage 7+]          ← BP-020 rendering contract
    skill-kpi-design        [Stage 7+]          ← BP-017 artifact writer (universal per v3)
    skill-description-triggers [Stage 7+]       ← BP-019 artifact writer (universal per v3)

Conditional (built as first trait exercises each):
    has_phases       → skill-phase-designer    [adds BP-009, BP-010, BP-011-016 if has_hitl]
    has_references   → skill-references-scaffolder extensions
    is_scheduled     → skill-cron-observability
    invokes_skills   → driver-level Agent spawning; signed handoffs if has_phases too

Optimization-run sub-skills (CLI --polish-* flags, not traits):
    skill-autoresearch-gate   — gated by --polish-autoresearch + BP-018
    skill-eval-loop           — gated by --polish-benchmark

Build priority (concrete):
    Stage 4: spec authoring ergonomics (client-spec-template.md + example + anti-patterns)
    Stage 5: skill-factory DRIVER skeleton (6-phase spine, universal-always-fire logic)
    Stage 6: skill-frontmatter (proves Agent-tool composition)
    Stage 7+: remaining universals, then conditionals as real client-spec exercises them
```

The old "15-archetype manifest" model is retired. Sub-skills activate from trait predicates, not archetype names.
