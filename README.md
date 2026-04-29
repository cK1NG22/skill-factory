# skill-factory

[![CI](https://github.com/ck22coding/skill-factory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ck22coding/skill-factory/actions/workflows/ci.yml)

A composable factory for authoring Claude Code skills from a single input spec — hands-off, trait-classified, compliance-gated. Has shipped 2 client deliveries (`acme-board-memo`, `discovery-call-prep`) end-to-end, hands-off after spec validation.

## What this is

`skill-factory` is a **driver skill** plus a set of **reusable sub-skills**. You feed it a `client-spec.md`. The driver classifies the target skill against **5 trait predicates** (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills` — Frame C, locked by ADR-0001), unions the sub-skills whose traits fire, runs each as an isolated Agent subagent over a driver-materialized context pack, assembles the output, runs it through a 13-check compliance gate, and lands the result in a per-client git repo as a working `~/.claude/skills/<slug>` symlink.

When a sub-skill improves, every trait whose firing-set includes it inherits the upgrade automatically. When a new authoring best-practice is discovered, it gets a `BP-###` entry under `patterns/` and the relevant sub-skill enforces it from then on.

## The vision: hands-off

The factory's north-star is **one human touchpoint per skill: the input spec.** Past the spec, the pipeline runs without supervision. This means spec quality is the entire quality ceiling — every ambiguity in the spec becomes a wrong sub-skill output downstream. So the factory's first sub-skill is `skill-spec-validator`: it either green-lights the spec or returns surgical gap-fills for you to address before it ever reaches the rest of the pipeline. No mid-pipeline pauses, no rubber-stamp gates, no "Claude asks 30 clarifying questions" — the spec answers everything.

If the spec is good, the factory commits to producing a 13/13-compliant skill end-to-end. If a sub-skill mid-pipeline hits ambiguity it can't resolve, that's a validator miss — routed back as a gap-report so the validator gets smarter on the next run.

## Architecture

```
client-spec.md  ──►  /skill-factory <slug> <spec-path>
                        │
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 1: validate         │  ──►  skill-spec-validator (Agent)
                 └────────────────────────────┘            │
                        │                                  ├─ STATUS: pass → continue
                        │                                  └─ STATUS: gaps → exit with fix-list
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 2: classify traits  │  ──►  trait_predicates.py → classifier.json
                 │  (5 boolean predicates)    │       (has_references / has_phases / has_hitl /
                 └────────────────────────────┘        is_scheduled / invokes_skills — Frame C)
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 3: materialize      │  ──►  build_context_pack.py renders one
                 │  context packs             │       phases/<NN>-<sub-skill>/input.md per
                 └────────────────────────────┘       firing trait — sub-skills read ONLY their pack (BP-033)
                        ▼
                 ┌────────────────────────────┐  • skill-frontmatter (always)
                 │  Phases 4–6: spawn         │  • skill-phase-designer (has_phases)
                 │  sub-skill Agents          │  • skill-references-scaffolder (has_references)
                 │  in parallel               │  • skill-cron-observability (is_scheduled)
                 └────────────────────────────┘  • skill-signed-handoff (has_phases ∧ invokes_skills)
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 8a: assemble        │  ──►  assemble_skill.py merges phase outputs → draft
                 │  Phase 8b: compliance gate │       skill-compliance-gate (13 checks, factory-internal
                 └────────────────────────────┘       artifacts skip Check 14 via meta-skill: true)
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 9: materialize      │  ──►  materialize_skill.py creates per-client repo
                 │  per-client + install      │       (~/Projects/<owner>-claude-skills/), copies skill,
                 └────────────────────────────┘       symlinks ~/.claude/skills/<slug>, gh repo create + push
                        ▼
                 ┌────────────────────────────┐
                 │  Phase 99: report          │  ──►  per-run summary written to ~/Claude/skill-factory/runs/
                 └────────────────────────────┘
```

## How to author a new client skill (5 steps)

1. **Write the spec.** Copy `skill-factory/assets/client-spec-template.md` into a working file (e.g., `~/Claude/specs/acme-board-memo.md`). Fill in every required section, including the optional `## Delivery / Remote repo: yes|no` line if you need to opt out of auto-publishing to GitHub.
2. **Validate the spec.** `/skill-spec-validator ~/Claude/specs/acme-board-memo.md` — get a pass or a gap-report.
3. **Run the factory.** `/skill-factory acme-board-memo ~/Claude/specs/acme-board-memo.md` — sit back.
4. **Receive the result.** Factory creates (or reuses) `~/Projects/<owner>-claude-skills/`, lands the skill at `<slug>/`, commits (and pushes if `Remote repo: yes`), and symlinks `~/.claude/skills/<slug>`.
5. **Use it.** `/<slug> <args>` works immediately. Two real deliveries (`acme-board-memo`, `discovery-call-prep`) shipped this way.

## How to add or modify a sub-skill

See `CONTRIBUTING.md` for the full workflow. Short version:

1. **Pattern first, code second.** If your change introduces a new authoring discipline, add an entry to `PATTERNS.md` (`BP-###`) before any code.
2. **Sub-skill first, trait second.** If your change adds a new sub-skill, add an entry to `SKILLS.md` describing its purpose, contract, which patterns it enforces, and which trait predicate(s) fire it, before authoring the SKILL.md itself.
3. **Fixtures required.** Every sub-skill ships with `references/fixtures/input.md` + `expected-output.md`. No exceptions.
4. **Run compliance locally.** `/skill-compliance ~/Projects/skill-factory/skill-<your-skill>/` must pass 13/13.

## Repo layout

```
skill-factory/                   ← this repo (private, ck22coding/skill-factory)
├── README.md                    ← you are here
├── PATTERNS.md                  ← best-practices catalog (BP-### entries)
├── SKILLS.md                    ← sub-skill catalog (purpose + enforcement)
├── CONTRIBUTING.md              ← collaborator workflow
├── skill-factory/               ← THE DRIVER skill
│   ├── SKILL.md
│   ├── references/
│   ├── assets/
│   └── scripts/
├── skill-spec-validator/        ← gates pipeline on input quality (Stage 3)
├── skill-frontmatter/           ← (Stage 6+)
├── skill-description-triggers/  ← (later)
├── ... (9 sub-skills shipped + driver-integrated; new traits add new sub-skills under Frame C)
└── skill-compliance/            ← 13-check audit (migrated from ~/.claude/skills/, Stage 2)

~/.claude/skills/                ← install layer: symlinks into this repo
├── skill-factory → ~/Projects/skill-factory/skill-factory
├── skill-spec-validator → ~/Projects/skill-factory/skill-spec-validator
└── ... (one symlink per sub-skill, added as each one ships)

~/Projects/<company>-claude-skills/   ← per-client output repos (auto-created by factory)
```

## Dependencies

- **Claude Code** — this is a Claude Code skill suite.
- **`gh` CLI authenticated** — required for auto-creating per-client repos.
- **Wrapped existing skills** (must be installed):
  - `/skill-creator` (Anthropic) — wrapped by `skill-eval-loop` + `skill-description-triggers` for optional polish.
  - `/kpi-setter` — wrapped by `skill-kpi-design`.
  - `/autoresearch` — wrapped by `skill-autoresearch-gate`.

## Status

The factory has shipped through **Stage 12 + finish-the-factory Phase 3** (2026-04-28). It is a **delivery system** — the full pipeline runs end-to-end from spec to installed skill on disk + symlinked into `~/.claude/skills/`, gate-clean, hands-off after the Phase 1 spec-validator gate.

| Milestone | Outcome |
|---|---|
| Stage 2: `/skill-compliance` migrated into repo | ✓ shipped |
| Stage 3: `skill-spec-validator` end-to-end (template sub-skill) | ✓ shipped |
| Stage 3.5: Frame C lock (rule engine over 5 traits, ADR-0001) | ✓ shipped — retired the 15-archetype taxonomy |
| Stage 4: Spec authoring aids (template + example + anti-patterns) | ✓ shipped — 3/3 pass `/skill-spec-validator` |
| Stage 6a/6b: `skill-frontmatter` standalone + driver-wired | ✓ shipped — proved Agent-tool composition |
| Stage 7a/7b: `skill-phase-designer` standalone + driver-wired | ✓ shipped |
| Stage 8c: `skill-signed-handoff` standalone | ✓ shipped |
| Stage 9a/9b: `skill-references-scaffolder` + `skill-cron-observability` shipped, signed-handoff driver-wired | ✓ shipped — all conditional sub-skills driver-integrated |
| Stage 9c: Self-bootstrap dogfood — factory reproduces itself | ✓ shipped — Principle D satisfied |
| Stage 10a/10b/10c: `skill-compliance-gate` standalone + driver-wired + meta-skill exception | ✓ shipped — bonus-sweep invariant: 9/9 factory artifacts pass their own gate |
| Stage 11a/11b/11c: `materialize_skill.py` + Phase 9 driver wiring + first real client delivery | ✓ shipped — `acme-board-memo` installed |
| Stage 11e: Second client delivery from a Notion-sourced spec | ✓ shipped — `discovery-call-prep` installed |
| Stage 12: Polish wave (slug pattern + materializer fixes) | ✓ shipped |
| Finish-the-factory wave (post-Stage-12) | Phases 1–3 ✓ shipped (cleanup, BP cross-citation, portable fixture paths); Phases 4–7 in flight (doc realignment, open-decision wave, live verifications, v1.0 tag) |

**Headline numbers**
- 9 sub-skills shipped + all driver-integrated + all gate-passing
- 2 client skills delivered (`acme-board-memo`, `discovery-call-prep`)
- 2 per-client repos materialized (`~/Projects/acme-claude-skills/` local-only; `ck22coding/optimal-skills` PRIVATE on GitHub)
- 38 best-practices codified (12 Universal / 11 Conditional / 15 Meta) under `patterns/`
- 367 tests across 7 sub-skill suites

## Glossary

- **Driver** — the top-level `/skill-factory` skill that orchestrates everything.
- **Sub-skill** — a single-responsibility authoring utility (e.g., `skill-frontmatter`, `skill-phase-designer`). Independently invocable as a slash command; also Agent-spawned by the driver.
- **Trait** — one of 5 boolean predicates the driver classifies a spec against (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`). Sub-skills fire when their associated trait fires. Locked by ADR-0001 (Frame C); the old 15-archetype taxonomy is retired.
- **Spec** — a `client-spec.md` file describing the target skill. The single human touchpoint.
- **Gate** — a hard checkpoint. The factory has two: `skill-spec-validator` (Phase 1) and `skill-compliance-gate` (Phase 8b).
- **Pattern (BP-###)** — a documented best-practice under `patterns/`. Sub-skills enforce them; the patterns directory has 12 Universal / 11 Conditional / 15 Meta files plus a template.
- **Meta-skill marker** — a `meta-skill: true` line in a SKILL.md frontmatter that tells `skill-compliance-gate` this artifact is factory-internal (not a client deliverable) and should skip Check 14 (BP-033 leakage rule). Stage 10c introduced; lets the factory's own 9 artifacts pass their own gate.
- **Session workspace** — `~/Claude/skill-factory/<slug>-<timestamp>/`, the filesystem data bus between driver and sub-skills.
- **Per-client repo** — `~/Projects/<owner>-claude-skills/` (e.g. `acme-claude-skills/`, `optimal-skills/`), auto-created by Phase 9. Houses one or more shipped client skills; optionally pushed to GitHub via `gh` CLI based on the spec's `## Delivery / Remote repo` line.

## Why this is so in-depth

Honest answer: skill authoring has a lot of well-known sharp edges (description-triggering, frontmatter compliance, output contracts, KPI vagueness, knowledge-mapping, signed handoffs), and most of them have been learned the hard way on prior projects (411 Suite, gstack, autoresearch). The factory is in-depth because it bakes those lessons into machinery instead of asking each new client skill to relearn them. `PATTERNS.md` is the running list of those lessons; `SKILLS.md` shows which sub-skill enforces which pattern. If you can read those two files in 10 minutes, the rest of the system makes sense.
