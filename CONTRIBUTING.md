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
   - `~/Projects/skill-factory/skill-<name>/SKILL.md` (frontmatter + 180–220 line traffic director per BP-006)
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
