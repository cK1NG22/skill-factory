# Expected output — passing-input.md

When `skill-cron-observability` runs against `fixtures/passing-input.md`, it should produce an `instrumentation-snippet.md` whose fenced Python block passes `observability_lint.py`:

```json
{"passed": true, "fails": []}
```

## Acceptance criteria

1. `instrumentation-snippet.md` exists and contains at least one fenced ```python block.
2. The snippet writes `result.json` under `~/Claude/acme-weekly-digest/runs/<timestamp>/` (Rule A).
3. The snippet writes an artifact file (`.md` extension per the spec) in the same directory (Rule B).
4. The snippet maintains a `~/Claude/acme-weekly-digest/latest.json` symlink (Rule C).
5. The `result.json` content includes keys `last_run`, `success`, `artifact_path` (Rule D).
6. Running `observability_lint.py instrumentation-snippet.md` returns exit code 0 and `passed: true`.
7. `notes.md` contains no `BLOCKER:` line. It may include informational observations (e.g. "lint passed; 4/4 rules satisfied").

## Lint-authoritative check

The generated snippet must satisfy the lint bit-for-bit. Do NOT substitute `"ok"` for `"success"`, `"ran_at"` for `"last_run"`, or `"output_path"` for `"artifact_path"`. Those exact keys are the contract.
