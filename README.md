# skill-factory

A composable factory for authoring Claude Code skills from a single input spec — hands-off, archetype-aware, compliance-gated.

## What this is

`skill-factory` is a **driver skill** plus a set of **reusable sub-skills**. You feed it a `client-spec.md`. It classifies the target skill into one of 15 archetypes, runs that archetype's pipeline of sub-skills (each encoding one well-tested authoring best-practice), assembles the output, runs it through a 13-check compliance gate, and lands the result in a per-client git repo as a working `~/.claude/skills/<company>-<slug>/` symlink.

When a sub-skill improves, every archetype that uses it inherits the upgrade automatically. When a new authoring best-practice is discovered, it gets a `BP-###` entry in `PATTERNS.md` and the relevant sub-skill enforces it from then on.

## The vision: hands-off

The factory's north-star is **one human touchpoint per skill: the input spec.** Past the spec, the pipeline runs without supervision. This means spec quality is the entire quality ceiling — every ambiguity in the spec becomes a wrong sub-skill output downstream. So the factory's first sub-skill is `skill-spec-validator`: it either green-lights the spec or returns surgical gap-fills for you to address before it ever reaches the rest of the pipeline. No mid-pipeline pauses, no rubber-stamp gates, no "Claude asks 30 clarifying questions" — the spec answers everything.

If the spec is good, the factory commits to producing a 13/13-compliant skill end-to-end. If a sub-skill mid-pipeline hits ambiguity it can't resolve, that's a validator miss — routed back as a gap-report so the validator gets smarter on the next run.

## Architecture

```
client-spec.md  ──►  /skill-factory <company> <spec>
                        │
                        ▼
                 ┌──────────────────────┐
                 │  Phase 1: validate   │  ──►  skill-spec-validator (Agent)
                 └──────────────────────┘            │
                        │                            ├─ STATUS: pass → continue
                        │                            └─ STATUS: gaps → exit cleanly with fix-list
                        ▼
                 ┌──────────────────────┐
                 │  Phase 2: classify   │  ──►  archetype-rubric.md → archetype.json
                 └──────────────────────┘
                        ▼
                 ┌──────────────────────┐
                 │  Phase 3: load       │  ──►  references/archetypes/<archetype>.md
                 │       manifest       │       → manifest.json (sub-skill sequence)
                 └──────────────────────┘
                        ▼
                 ┌──────────────────────┐
                 │  Phase 4: invoke     │  ──►  per sub-skill in manifest:
                 │  sub-skills (Agent)  │         spawn Agent → write phase output
                 └──────────────────────┘            │
                        │                            ├─ skill-frontmatter
                        │                            ├─ skill-knowledge-mapper
                        │                            ├─ skill-output-contract
                        │                            └─ ... (per archetype)
                        ▼
                 ┌──────────────────────┐
                 │  Phase 5: assemble   │  ──►  skill-references-scaffolder merges →
                 │  + compliance gate   │       skill-compliance (13/13)
                 └──────────────────────┘
                        ▼
                 ┌──────────────────────┐
                 │  Phase 6: materialize│  ──►  ensure ~/Projects/<company>-claude-skills/
                 │  + optional polish   │       move draft, commit+push, symlink ~/.claude/skills/
                 └──────────────────────┘            │
                                                    └─ optional: skill-eval-loop, skill-autoresearch-gate
```

## How to author a new client skill (5 steps)

1. **Write the spec.** Copy `skill-factory/assets/client-spec-template.md` into a working file (e.g., `~/Claude/specs/acme-onboarding.md`). Fill in every required section. The template comments explain what each section needs.
2. **Validate the spec.** `/skill-spec-validator ~/Claude/specs/acme-onboarding.md` — get a pass or a gap-report.
3. **Run the factory.** `/skill-factory acme ~/Claude/specs/acme-onboarding.md` — sit back.
4. **Receive the result.** Factory creates (or reuses) `~/Projects/acme-claude-skills/`, lands the new skill at `acme-onboarding/`, commits + pushes, and symlinks `~/.claude/skills/acme-onboarding`.
5. **Use it.** `/acme-onboarding <args>` works immediately.

## How to add or modify a sub-skill

See `CONTRIBUTING.md` for the full workflow. Short version:

1. **Pattern first, code second.** If your change introduces a new authoring discipline, add an entry to `PATTERNS.md` (`BP-###`) before any code.
2. **Sub-skill first, archetype second.** If your change adds a new sub-skill, add an entry to `SKILLS.md` describing its purpose, contract, and which patterns it enforces, before authoring the SKILL.md itself.
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
├── ... (15 sub-skills total, built incrementally)
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

## Status & roadmap

| Stage | What | Status |
|---|---|---|
| 1 | Repo + thinking docs (this) | **In progress** |
| 2 | Migrate `/skill-compliance` into the repo | Pending |
| 3 | Build `skill-spec-validator` end-to-end (template sub-skill) | Pending |
| 4 | Spec authoring ergonomics (template + example + anti-patterns) | Pending |
| 5 | Driver SKILL.md skeleton + 1 archetype manifest | Pending |
| 6 | Build `skill-frontmatter` (proves composition) | Pending |
| 7–N | Remaining sub-skills for first archetype, one per stage | Pending |
| M | End-to-end MVP demo | Pending |
| M+1+ | Add archetypes one at a time | Pending |
| Final | Self-bootstrap dogfood — factory regenerates itself | Pending |

**First-archetype choice (transformation vs phased-HITL vs pipeline-orchestrator) is open** pending a Carter+Adam discussion.

## Glossary

- **Driver** — the top-level `/skill-factory` skill that orchestrates everything.
- **Sub-skill** — a single-responsibility authoring utility (e.g., `skill-frontmatter`, `skill-kpi-design`). Independently invocable.
- **Archetype** — one of 15 categories a target skill can fall into (transformation, phased-HITL, pipeline-orchestrator, etc.). Each has its own sub-skill sequence.
- **Manifest** — `references/archetypes/<archetype>.md`, declaring which sub-skills run in what order for that archetype.
- **Spec** — a `client-spec.md` file describing the target skill. The single human touchpoint.
- **Gate** — a hard checkpoint. The factory has two: `skill-spec-validator` (Phase 1) and `skill-compliance` (Phase 5).
- **Pattern (BP-###)** — a documented best-practice in `PATTERNS.md`. Sub-skills enforce them.
- **Session workspace** — `~/Claude/skill-factory/<slug>-<timestamp>/`, the filesystem data bus between driver and sub-skills.

## Why this is so in-depth

Honest answer: skill authoring has a lot of well-known sharp edges (description-triggering, frontmatter compliance, output contracts, KPI vagueness, knowledge-mapping, signed handoffs), and most of them have been learned the hard way on prior projects (411 Suite, gstack, autoresearch). The factory is in-depth because it bakes those lessons into machinery instead of asking each new client skill to relearn them. `PATTERNS.md` is the running list of those lessons; `SKILLS.md` shows which sub-skill enforces which pattern. If you can read those two files in 10 minutes, the rest of the system makes sense.
