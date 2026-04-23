# Expected output — passing-input.md

When `skill-signed-handoff` runs against `fixtures/passing-input.md`, it produces a `output-signature-template.py` whose source passes `handoff_lint.py`:

```json
{"passed": true, "fails": []}
```

## Acceptance criteria

1. `output-signature-template.py` exists and is valid Python (parses without syntax errors).
2. The file contains a top-level `SIGNED_FIELDS` list (or equivalent `*FIELD*` name) whose entries are exactly the three fields declared in `passing-input.md`:
   - `argument_flow`
   - `leadlines`
   - `recommendation`
3. The file accepts `--sign` and `--verify` modes (Rules A, B).
4. The file imports and calls `hashlib.sha256` (Rule C).
5. The file returns / `sys.exit`s each of `0`, `1`, `2`, `3` from a reachable branch (Rule E).
6. The file serializes the subset with `sort_keys=True` before hashing (Rule F).
7. Running `handoff_lint.py output-signature-template.py` returns `passed: true`.
8. `notes.md` contains no `BLOCKER:` line. It may include informational observations about the declared fields and the upstream/downstream phase bindings (`phase-6` → `phase-1`).

## Byte-level reference

A correct emission is checked in at `fixtures/passing-signature-script.py`. It is not required that the sub-skill produce byte-identical output (whitespace / comment formatting may differ), only that the stamped file lints clean.
