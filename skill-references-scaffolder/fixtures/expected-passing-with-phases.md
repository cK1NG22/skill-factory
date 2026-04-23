# Expected output — passing-with-phases-input.md

When `skill-references-scaffolder` runs against `fixtures/passing-with-phases-input.md`, the lint verdict on the target skill (`fixtures/passing-with-phases-skill/`) must be:

```json
{"passed": true, "fails": []}
```

Invocation:

```bash
python3 scripts/references_lint.py \
    fixtures/passing-with-phases-skill --has-references --has-phases
```

## Acceptance criteria

1. `phases/` and `references/` both exist at the skill root as siblings.
2. No nested `phases/*/references/` or `references/*/phases/` paths.
3. All three reference files are cited canonically in SKILL.md.
4. `assets/` is present → no missing-assets warning.
5. Lint returns `passed: true` with 0 fails.
6. `notes.md` contains no `BLOCKER:` line.
