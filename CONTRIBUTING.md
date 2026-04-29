# Contributing to skill-factory

Welcome. This doc covers how to set up the repo locally, how to propose changes, and the discipline that keeps the system coherent.

## Setup (one-time)

```bash
# Clone
git clone git@github.com:ck22coding/skill-factory.git ~/Projects/skill-factory
cd ~/Projects/skill-factory

# Install: symlink each skill into ~/.claude/skills/ so Claude Code picks them up
# (Add a symlink for each skill that exists in the repo today; new ones are added per stage)
for skill in skill-factory skill-spec-validator skill-frontmatter skill-compliance; do
  if [ -d "$skill" ]; then
    ln -sf "$PWD/$skill" "$HOME/.claude/skills/$skill"
  fi
done

# Verify
ls -la ~/.claude/skills/ | grep -E "skill-(factory|spec-validator|frontmatter|compliance)"
```

If you get permission errors, your existing `~/.claude/skills/skill-compliance/` may be a real directory that needs to be moved to a backup before symlinking. See Stage 2 in `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md` for the migration recipe.

### Activate the pre-commit hook (recommended)

The repo ships a fast pre-commit hook at `.githooks/pre-commit` that runs the driver canaries (`phase_lint` + `references_lint --strict-two-level`) plus a frontmatter lint on any staged `SKILL.md` files. Typical runtime is under one second.

```bash
git config core.hooksPath .githooks
```

That single command points git at the in-repo `.githooks/` directory, so the hook is picked up automatically and stays in sync as `git pull` brings in updates. Bypass once with `git commit --no-verify` if you genuinely need to (the full gauntlet + bonus-sweep run in CI on every PR per `.github/workflows/ci.yml`, so bypass-here-fix-later is a fine workflow).

## The PR discipline (read this before opening a PR)

The factory has three "thinking docs" that govern everything: **`PATTERNS.md`** (index of best practices, linking to per-BP files under `patterns/`), **`SKILLS.md`** (sub-skill catalog), and **`HUB.md`** (running progress log, canonical at repo root and symlinked into Carter's memory). Code changes should follow doc changes, not lead them.

### Adding a new pattern

As of Stage 3.5, patterns live as individual files under `patterns/` (with factory-internal BPs under `patterns/meta/`). `PATTERNS.md` is an index that links to them.

1. Pick the next free BP number.
2. Copy the template: `cp patterns/_template.md patterns/bp-<NNN>-<slug>.md` (or `patterns/meta/...` if the BP is factory-internal).
3. Fill every field (Source, Category, Why, When applicable, Enforced by, Correct, Incorrect).
4. Add the row to `PATTERNS.md` in the correct category section.
5. If the BP is Conditional, confirm the trait already exists in the 5-trait set (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`). Proposing a new trait requires justification in the PR.
6. Open PR titled `patterns: BP-### <short name>`.
7. The "Enforced by" field can be `none yet` if no sub-skill enforces it (TODO state).
8. Get review. Merge. Only then can a follow-up PR add the sub-skill code that enforces the pattern (per BP-030).

### Per-stage HUB.md update (required)

Every stage-shipping PR must also update `HUB.md`:

1. Add a new entry at the top of the "Progress log" section (newest first): stage number, date, commit sha placeholder, one-paragraph summary.
2. Update the "Status snapshot" counters if they changed.
3. Move completed TODOs from "In progress" to the progress-log entry, or strike them through.
4. Commit HUB.md changes in the SAME commit as the code. No orphan HUB entries.

### BP-034 discipline for new sub-skill PRs

Per BP-034, sub-skills are ONLY for cross-skill reuse. Before opening a PR that adds a new sub-skill:
- Identify which existing skills (2+) would reuse the proposed sub-skill.
- If you can't name 2 — stop. The sub-process belongs in a `references/<topic>.md` file inside the skill that needs it, not in its own directory.
- `/skill-spec-validator` catches this at Phase 1 for client skills being authored; reviewers catch it at PR time for factory sub-skills being added.

### Adding a new sub-skill

1. Open a PR adding an entry to `SKILLS.md` (purpose, inputs, outputs, enforces patterns, when invoked, standalone usable, status).
2. Get review on the conceptual model BEFORE writing any code.
3. Open the implementation PR:
   - `~/Projects/skill-factory/skill-<name>/SKILL.md` (frontmatter + traffic director sized per BP-006: 180–220 lines for single-Procedure shape, or ≤150 lines for phased-orchestrator shape per BP-037)
   - `~/Projects/skill-factory/skill-<name>/references/` (detail lives here per BP-007)
   - `~/Projects/skill-factory/skill-<name>/references/fixtures/input.md` + `expected-output.md` (REQUIRED — no sub-skill ships without fixtures)
4. Verify locally:
   - `/skill-compliance ~/Projects/skill-factory/skill-<name>/` passes 13/13
   - `/skill-<name>` runs against fixtures and matches expected output (diff)
5. Update `SKILLS.md` status: 🔵 Planned → 🟢 Live.
6. Symlink: `ln -sf ~/Projects/skill-factory/skill-<name> ~/.claude/skills/skill-<name>`
7. Commit + push.

### Modifying an existing sub-skill

1. If the change introduces a new authoring discipline, follow "Adding a new pattern" first.
2. Update `SKILLS.md` — at minimum, the "Enforces patterns" field if the BP set changes.
3. Update fixtures if behavior changed.
4. Verify compliance still passes.
5. Open PR with all changes in one commit (or one logical commit per concern).

### Adding a new archetype

1. Add archetype to `~/Projects/skill-factory/skill-factory/references/archetype-rubric.md` decision tree.
2. Add manifest at `~/Projects/skill-factory/skill-factory/references/archetypes/<archetype>.md` listing sub-skill sequence.
3. If the archetype needs sub-skills that don't exist yet, follow "Adding a new sub-skill" for each.
4. Add an end-to-end test spec at `~/Projects/skill-factory/skill-factory/assets/client-spec-examples/<archetype>-example.md`.
5. Run `/skill-factory <test-company> <example-spec>` and verify the output passes 13/13 compliance.

## Factory conventions (post-Stage-5)

Conventions that have solidified as the factory built its first two sub-skills (`skill-frontmatter` Stage 6a, `skill-phase-designer` Stage 7a). Apply these to every new sub-skill PR.

- **BP-033 — sub-skills read input.md only.** The driver's Phase 3 materializes a `phases/NN-<sub-skill>/input.md` pack containing the spec excerpt, classified traits, and an explicit list of BP file paths. Sub-skills open ONLY that `input.md` plus the BPs it names. They never walk `patterns/` directly. Sub-skill SKILL.md Step 1 must say so.
- **BP-034 — sub-skills only for cross-skill reuse.** If a sub-process would be used by exactly one parent, it belongs in that parent's `references/<topic>.md`, not in its own directory. `skill-spec-validator` enforces this against client specs at Phase 1 (filesystem-lookup against `~/.claude/skills/<name>/` — so the validator's behavior depends on the ecosystem's installed-skill state; a clean CI runner will reject specs that pass locally). Reviewers enforce this against factory PRs at review time.
- **Sub-skill build pattern.** Every sub-skill ships with: its own directory at repo root (sibling to other sub-skills, per BP-025); its own `SKILL.md` (traffic director, 180–220 lines for single-Procedure shape per BP-006, or ≤150 lines for phased-orchestrator shape per BP-037 — driver-style sub-skills are rare; most factory sub-skills are single-Procedure); its own `references/<rules>.md` (authoritative rules contract); its own `scripts/<lint>.py` (pure-stdlib deterministic check); its own fixtures at skill root per BP-032 (passing + gaps + expected-output oracles); and its own tests at `tests/test_<lint>.py`.
- **Stage cadence.** Each sub-skill stage goes: **build → live E2E (isolated Agent against every fixture) → audit sweep (unit tests + `/skill-compliance` + dogfood frontmatter lint on its own SKILL.md) → commit**. No scaffolding ahead of live consumers (BP-029).
- **Lint is authoritative.** If a lint script and a rules doc disagree, **update the doc to match the lint, not the lint to match the doc**. The rules doc is the human-facing teaching surface; the script is the enforced contract. This keeps drift one-directional.

## Stage cadence

This repo follows incremental-build discipline (BP-029). Build plan lives at `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md` (Carter's local plan file). Each "Stage" produces a working, committed, pushable artifact — never a half-built scaffold.

If you're starting work on a stage:
1. Confirm the previous stage was reviewed and merged.
2. State which stage you're starting in your PR title (e.g., "Stage 6 — author skill-frontmatter").
3. Don't start the next stage until the current one is reviewed.

## Local compliance check

```bash
cd ~/Projects/skill-factory
/skill-compliance .                                # checks all sub-skills in the repo
/skill-compliance ./skill-spec-validator           # checks one
```

If `/skill-compliance` isn't on your `PATH`, invoke directly:
```bash
python ~/Projects/skill-factory/skill-compliance/scripts/compliance_check.py <path>
```

## Commit message convention

Short, imperative, scoped:
```
Stage 3: author skill-spec-validator with passing-spec fixture

Implements BP-026, BP-027, BP-028. Adds references/fixtures/passing-spec.md
and gaps-spec.md with expected outputs. Standalone test passes; symlink wired.
```

## Questions?

Open an issue at https://github.com/ck22coding/skill-factory/issues. Reference relevant `BP-###` numbers when proposing pattern changes.
