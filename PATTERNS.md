# PATTERNS — index

Best-practices catalog for `skill-factory`. Each row links to a dedicated file under `patterns/` (or `patterns/meta/` for factory-internal patterns).

**Discipline:**
- New pattern → copy `patterns/_template.md` → fill out → add the row below → PR titled `patterns: BP-### <short name>`.
- Only **then** can code that enforces the pattern be added (BP-030).
- A pattern that no sub-skill enforces is either a TODO (`**Enforced by:** none yet`) or removed.

**Buckets:**
- **Universal** — applies to every skill the factory produces. No decision logic needed; driver always enforces.
- **Conditional** — applies only when a trait fires from spec content. Trait names appear in the "Applies to" column.
- **Meta** — factory-internal discipline. Never applied to client skills. Lives in `patterns/meta/` for physical separation.

The 5 conditional traits: `has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`. Predicate definitions are PROVISIONAL until the BP × real-skill matrix exercise locks them (see ADR-0001 once authored).

---

## Frontmatter & description

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-001 | Trigger phrases in description | Universal | Every skill | [patterns/bp-001-trigger-phrases.md](patterns/bp-001-trigger-phrases.md) |
| BP-002 | Pushy description | Universal | Every skill | [patterns/bp-002-pushy-description.md](patterns/bp-002-pushy-description.md) |
| BP-003 | Name ≤64 chars, lowercase + hyphens | Universal | Every skill | [patterns/bp-003-name-rules.md](patterns/bp-003-name-rules.md) |
| BP-004 | Description ≤1024 chars | Universal | Every skill | [patterns/bp-004-description-length.md](patterns/bp-004-description-length.md) |
| BP-005 | `allowed-tools` declared | Universal | Every skill | [patterns/bp-005-allowed-tools.md](patterns/bp-005-allowed-tools.md) |

## File structure & references

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-006 | SKILL.md is a lean traffic director | Universal | Every skill (range calibrates) | [patterns/bp-006-lean-traffic-director.md](patterns/bp-006-lean-traffic-director.md) |
| BP-007 | Detail in `references/`, loaded on demand | Conditional | `has_references` | [patterns/bp-007-references-loaded-on-demand.md](patterns/bp-007-references-loaded-on-demand.md) |
| BP-008 | References one level deep | Universal | Every skill | [patterns/bp-008-references-one-level-deep.md](patterns/bp-008-references-one-level-deep.md) |
| BP-009 | Parallel folders (`phases/` + `references/` + `assets/`) | Conditional | `has_phases` | [patterns/bp-009-parallel-folders.md](patterns/bp-009-parallel-folders.md) |
| BP-010 | Apply once, carry forward, reference later | Conditional | `has_phases` | [patterns/bp-010-apply-once-carry-forward.md](patterns/bp-010-apply-once-carry-forward.md) |

## Workflow & human-in-the-loop

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-011 | Announce phase transitions | Conditional | `has_hitl` | [patterns/bp-011-announce-phase-transitions.md](patterns/bp-011-announce-phase-transitions.md) |
| BP-012 | Hard gates ("Do NOT proceed…") | Conditional | `has_hitl` | [patterns/bp-012-hard-gates.md](patterns/bp-012-hard-gates.md) |
| BP-013 | Ask user first, then suggest | Conditional | `has_hitl` | [patterns/bp-013-ask-user-first.md](patterns/bp-013-ask-user-first.md) |
| BP-014 | Rationale with "because" | Universal | Every skill | [patterns/bp-014-rationale-with-because.md](patterns/bp-014-rationale-with-because.md) |
| BP-015 | Number questions, use `AskUserQuestion` | Conditional | `has_hitl` | [patterns/bp-015-number-questions.md](patterns/bp-015-number-questions.md) |
| BP-016 | Inline question rule (≤4 short questions) | Conditional | `has_hitl` | [patterns/bp-016-inline-question-rule.md](patterns/bp-016-inline-question-rule.md) |

## KPIs & evaluation

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-017 | KPIs are Observable/Specific/Not-gameable/Not-compound | Universal (artifact) | Every skill writes kpi.md | [patterns/bp-017-kpi-rubric.md](patterns/bp-017-kpi-rubric.md) |
| BP-019 | Eval test cases (realistic + near-miss negatives) | Universal (artifact) | Every skill writes trigger-evals | [patterns/bp-019-eval-test-cases.md](patterns/bp-019-eval-test-cases.md) |

*BP-018 is Meta — see below.*

## Output & rendering

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-020 | Write output contract FIRST (calibrated by complexity) | Universal | Every skill | [patterns/bp-020-output-contract-first.md](patterns/bp-020-output-contract-first.md) |
| BP-021 | Outputs go to `~/Claude/<skill>/` | Universal | Every file-writing skill | [patterns/bp-021-output-home.md](patterns/bp-021-output-home.md) |
| BP-022 | Cron observability (last-run, success, artifact location) | Conditional | `is_scheduled` | [patterns/bp-022-cron-observability.md](patterns/bp-022-cron-observability.md) |

## Composition & pipelines

| BP | Name | Bucket | Applies to | File |
|---|---|---|---|---|
| BP-023 | Sub-skill composition via `Agent` tool | Conditional | `invokes_skills` | [patterns/bp-023-agent-composition.md](patterns/bp-023-agent-composition.md) |
| BP-024 | Signed handoffs between pipeline skills | Conditional | `has_phases` ∧ `invokes_skills` | [patterns/bp-024-signed-handoffs.md](patterns/bp-024-signed-handoffs.md) |

*BP-025 and BP-034 are Meta — see below.*

---

## Meta (factory-internal) — `patterns/meta/`

Never applied to client skills. Govern how the factory itself is built and operated.

| BP | Name | Scope | File |
|---|---|---|---|
| BP-018 | KPI before autoresearch (polish guard) | `--polish-autoresearch` invocations | [patterns/meta/bp-018-kpi-before-autoresearch.md](patterns/meta/bp-018-kpi-before-autoresearch.md) |
| BP-025 | Sub-skills are siblings (top-level), not nested | Factory architecture | [patterns/meta/bp-025-siblings-not-nested.md](patterns/meta/bp-025-siblings-not-nested.md) |
| BP-026 | Sole human touchpoint = the input spec | Factory driver design | [patterns/meta/bp-026-sole-human-touchpoint.md](patterns/meta/bp-026-sole-human-touchpoint.md) |
| BP-027 | Input gate before classify | Factory Phase 1 | [patterns/meta/bp-027-input-gate-before-classify.md](patterns/meta/bp-027-input-gate-before-classify.md) |
| BP-028 | `BLOCKER:` convention — no silent failures | Factory sub-skill discipline | [patterns/meta/bp-028-blocker-convention.md](patterns/meta/bp-028-blocker-convention.md) |
| BP-029 | Build incrementally — no scaffold-and-fill | Factory dev process | [patterns/meta/bp-029-build-incrementally.md](patterns/meta/bp-029-build-incrementally.md) |
| BP-030 | Pattern first, code second | Factory PR workflow | [patterns/meta/bp-030-pattern-first-code-second.md](patterns/meta/bp-030-pattern-first-code-second.md) |
| BP-031 | Co-locate co-evolving tools in one repo | Factory repo organization | [patterns/meta/bp-031-colocate-coevolving.md](patterns/meta/bp-031-colocate-coevolving.md) |
| BP-032 | Fixtures at skill root, not under references/ | Factory sub-skill layout | [patterns/meta/bp-032-fixtures-at-skill-root.md](patterns/meta/bp-032-fixtures-at-skill-root.md) |
| BP-033 | Driver-materialized context packs | Factory driver discipline | [patterns/meta/bp-033-driver-context-packs.md](patterns/meta/bp-033-driver-context-packs.md) |
| BP-034 | Sub-skills only for cross-skill reuse | Authoring discipline | [patterns/meta/bp-034-subskill-vs-reference.md](patterns/meta/bp-034-subskill-vs-reference.md) |
| BP-035 | No factory preamble (no gstack-style bash header) | Factory output shape | [patterns/meta/bp-035-no-factory-preamble.md](patterns/meta/bp-035-no-factory-preamble.md) |
| BP-036 | Predicate registry for compound sub-skill triggers | Factory driver gating | [patterns/meta/bp-036-predicate-registry.md](patterns/meta/bp-036-predicate-registry.md) |
| BP-037 | Thin top-director SKILL.md (two-level director hierarchy) | Factory architecture | [patterns/meta/bp-037-thin-director.md](patterns/meta/bp-037-thin-director.md) |
| BP-038 | Self-bootstrap acceptance criterion | Factory verification | [patterns/meta/bp-038-self-bootstrap.md](patterns/meta/bp-038-self-bootstrap.md) |

---

## Summary counts

- **Universal:** 12 BPs (enforced on every client skill)
- **Conditional:** 11 BPs (fired by 5 traits)
- **Meta:** 15 BPs (factory-internal, never applied to client skills)
- **Total:** 38 BPs + 1 template

## Pattern numbering reservations

- BP-001 to BP-099: stable, currently in use.
- BP-100 to BP-199: reserved for archetype-specific patterns (added if/when a specific archetype shape forces its own rules — expected rare under the Frame C rule-engine model).
- BP-200+: experimental / deprecated patterns kept for historical reference.

When deprecating a pattern, mark its file with `**Status: deprecated as of YYYY-MM-DD — see BP-NNN for replacement.**` and update this index's row. Don't delete the file; downstream code may still reference the number.

## How to add a pattern

1. `cp patterns/_template.md patterns/bp-<next-number>-<slug>.md` (or `patterns/meta/...` for Meta BPs).
2. Fill every field (Source, Category, Why, When applicable, Enforced by, Correct, Incorrect).
3. Add a row to this index in the correct category section.
4. If Conditional, confirm the trait already exists in the 5-trait set or propose a new one (rare — requires justification in the PR).
5. Submit PR titled `patterns: BP-### <short name>`.
6. Only after merge can code that enforces the pattern be added (BP-030).
