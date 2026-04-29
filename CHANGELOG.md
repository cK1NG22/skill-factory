# Changelog

All notable changes to the Skill Factory.

This project follows [Semantic Versioning](https://semver.org/). v1.0 anchors "first shipped version" per [ADR-0002](docs/decisions/ADR-0002-v1.0-success-criteria.md): 9 sub-skills driver-integrated and gate-clean, 2 real client deliveries, the bonus-sweep self-acceptance invariant satisfied.

## [1.0.0] — 2026-04-29

First shipped version. The factory authors a Claude Code skill end-to-end from a validated `client-spec.md`: validates the spec, classifies traits, materializes per-phase context packs, spawns sub-skill Agents, assembles the result, gates it for compliance, and (when the spec opts in) materializes a per-client repo with a `gh repo create --private` push.

### Architecture

- **Frame C — rule engine over 5 provisional traits.** `has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`. The fixed 15-archetype taxonomy was retired at Stage 3.5; new traits or BP intersections add new sub-skills as real client specs exercise them. See [ADR-0001](docs/decisions/ADR-0001-frame-c-rule-engine.md).
- **Two-level director hierarchy.** Top `SKILL.md` → 10 `phases/<N>-<name>/director.md` files (01–09 + 99) → phase-scoped `phases/<N>-<name>/references/`. Cross-phase mechanics in `skill-factory/references/`. Enforced at source-control level by `references_lint.py --strict-two-level`.
- **38 BPs codified** (12 Universal / 11 Conditional / 15 Meta). `patterns/meta/` physically separates factory-internal BPs from client-applicable ones.

### Sub-skills shipped (9, all driver-integrated and gate-passing)

`skill-compliance`, `skill-spec-validator`, `skill-factory` (driver), `skill-frontmatter`, `skill-phase-designer`, `skill-references-scaffolder`, `skill-cron-observability`, `skill-signed-handoff`, `skill-compliance-gate`. Every artifact carries `meta-skill: true` in frontmatter; the bonus-sweep invariant — factory artifacts pass their own gate — is **9 / 9**.

### Client deliveries (2 real)

- `acme-board-memo` (Stage 11c) — installed at `~/Projects/acme-claude-skills/` + symlinked into `~/.claude/skills/`. Local-only; `gh` opted out via spec's `## Delivery / Remote repo: no`.
- `discovery-call-prep` (Stage 11e) — installed at `~/Projects/optimal-claude-skills/`. PRIVATE GitHub repo `ck22coding/optimal-skills` with `adamkingai` collaborator (Notion-sourced spec).

### Tests

**367 / 367 across 7 suites** (22 frontmatter + 33 phase-designer + 51 references-scaffolder + 28 cron-observability + 36 signed-handoff + 163 skill-factory + 34 compliance-gate). Driver canaries green: `phase_lint` reports 10 sequential steps; `references_lint --strict-two-level` reports 10 phase directors + flat 5-file `references/`.

### Known unverified at v1.0

- **Live Agent self-bootstrap E2E (Verification C of Phase 6).** The diff tool's `verdict: "pass"` and the Stage 10c gate-verdict-match invariant (regenerated and committed both gate-clean) were confirmed via subagent. The subagent executed sub-skill roles inline rather than spawning live Agent-tool subtasks, so the live-Agent-spawn mechanics are taken on faith. The factory's per-phase contracts are sufficiently specified that an LLM reading the SKILL.md can produce byte-equivalent outputs — but the live Agent-spawn path itself is not E2E-proved at v1.0.
- **Live `gh_ensure_local_origin` smoke (Verification B of Phase 6).** Function logic at `materialize_skill.py:283-322` carries inline Stage 11e regression context. The reconcile path was not exercised against a fresh repo at v1.0 — the existing `~/Projects/optimal-claude-skills/` already has origin wired (function short-circuits), and the planned discovery-call-prep spec re-run proved unworkable because the spec is no longer on disk.
- **Stage 11d `test-acme-claude-skills` repo cleanup (Verification A of Phase 6).** Local `~/Projects/test-acme-claude-skills/` and the GitHub repo `ck22coding/test-acme-claude-skills` survive v1.0. Carter's `gh` token lacks `delete_repo` scope; UI-delete or `gh auth refresh -h github.com -s delete_repo` is the remediation.

### Deferred post-v1.0

Per ADR-0002:

- BP-006 ↔ Principle E body-size band reconciliation. The driver SKILL.md's 130-line body sits at the lower edge of BP-006's 180–220 band but well within Principle E's ≤150. Documented as dormant doc-debt; the gate is 9/9 PASS, no runtime failure.
- Stage 13 skill-compliance rule additions. Proposal #1 (BP-033 leakage check, future Check 15) and Proposal #2 (cross-scope meta-skill check, future Check 16) are drafted at `~/.claude/plans/phase-5-skill-compliance-additions.md`.
- CI on PRs.
- Pre-commit hook.

### Notable stages on the path here

- **Stage 3.5** — Frame C decision (15-archetype taxonomy retired); patterns broken into per-BP files.
- **Stages 6a / 6b / 7a / 7b** — frontmatter and phase-designer sub-skills shipped standalone and driver-integrated.
- **Stages 8a / 8b / 8c** — references-scaffolder, cron-observability, and signed-handoff sub-skills shipped standalone.
- **Stage 9.0** — adopted two-level director hierarchy (Principle F); driver SKILL.md thinned 201 → 113 body-lines.
- **Stages 9a / 9b / 9c** — wired references-scaffolder + cron-observability (9a), signed-handoff with predicate registry (9b), self-bootstrap diff tool (9c).
- **Stages 10a / 10b / 10c** — `skill-compliance-gate` standalone, driver-integrated as Phase 8, meta-skill exception for factory-internal artifacts.
- **Stages 11.0 / 11a / 11b / 11c / 11d / 11e** — `materialize_skill.py` shipped, wired into the driver as Phase 9, first real client delivery (acme-board-memo, local-only), live `gh` E2E (test-acme), second client delivery (discovery-call-prep, GitHub-PRIVATE-with-collaborator).
- **Stage 12** — polish wave: bare-slug pattern, README YAML leak fix, collaborator-status disambiguation, `gh_ensure_local_origin` reconcile helper.
- **Finish-the-factory wave (Phases 1–7)** — mechanical cleanup, BP-035/036/037/038 cross-citation, portable `{{REPO_ROOT}}` fixture paths, post-Stage-3.5 doc realignment, open-decision drafting (ADR-0002 + Stage 13 plan), live verifications, v1.0 tag.

[1.0.0]: https://github.com/ck22coding/skill-factory/releases/tag/v1.0.0
