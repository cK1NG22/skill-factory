# Expected output — passing-input.md

When `skill-references-scaffolder` runs against `fixtures/passing-input.md`, the lint verdict on the target skill (`fixtures/passing-skill/`) must be:

```json
{"passed": true, "fails": []}
```

Invocation:

```bash
python3 scripts/references_lint.py \
    fixtures/passing-skill --has-references
```

## Acceptance criteria

1. All three reference files (`scoping-questions.md`, `strategy-overview.md`, `anti-patterns.md`) are cited in the target SKILL.md using one of the canonical verbs (`Read`, `See`, `Consult`, `Load`, `Use`, `Refer to`, `per`).
2. No sub-directories under `references/`.
3. No inline tables >= 10 rows in SKILL.md.
4. No dense-prose spans >= 20 lines in SKILL.md.
5. Lint returns `passed: true` with 0 fails.
6. `notes.md` contains no `BLOCKER:` line.
