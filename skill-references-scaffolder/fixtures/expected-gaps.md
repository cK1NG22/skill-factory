# Expected output — gaps-input.md

When `skill-references-scaffolder` runs against `fixtures/gaps-input.md`, the lint verdict on the target skill (`fixtures/gaps-skill/`) must be:

```json
{"passed": false}
```

Invocation:

```bash
python3 scripts/references_lint.py \
    fixtures/gaps-skill --has-references --has-phases
```

## Acceptance criteria (expected fails)

The lint output must contain at least these failure categories in `fails`:

1. **BP-008 violation** — `references/nested-oops/` is a sub-directory of `references/`.
2. **BP-007 uncited file** — `anti-patterns.md` is present under `references/` but the target SKILL.md never cites it.
3. **BP-007 inline content** — the target SKILL.md contains a >= 10-row pipe-delimited table that must be moved to `references/<topic>.md`.
4. **BP-009 nested parallel folder** — `phases/01-intake/references/` violates the sibling rule.

## notes.md

Must contain at least one `BLOCKER:` line referencing the sub-directory nesting (BP-008) or the two-failure retry cap (BP-028), since auto-flattening is prohibited.

## Why this fixture matters

- Proves Rule A (BP-008) catches sub-directory nesting even when the file names look innocent.
- Proves Rule B (BP-007) distinguishes an orphan reference file from a cited one.
- Proves Rule B's inline-content detection catches a 40-row table pasted directly into SKILL.md.
- Proves Rule C (BP-009) catches `phases/*/references/` nesting.
- Proves strict-stop discipline — the sub-skill refuses to auto-move files or delete orphans.
