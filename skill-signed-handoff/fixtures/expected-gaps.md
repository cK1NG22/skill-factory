# Expected output — gaps-input.md

When `skill-signed-handoff` runs against `fixtures/gaps-input.md`, it should fail fast at Step 4 of its procedure (spec declares zero argument-bearing fields; a signed handoff over nothing is useless).

## notes.md

Must contain a `BLOCKER:` line like:

```
BLOCKER: spec declares no argument-bearing fields; signed handoff is meaningless without them
```

The exact wording may vary but must:
1. Begin with `BLOCKER:`.
2. Name the "no argument-bearing fields" condition.
3. Implicate the upstream spec author / spec-validator (not silently invent a fake field list).

## output-signature-template.py

**NOT produced** — or produced empty / with the unstamped placeholder still in place. Acceptance is "no viable signature script generated from an empty-field spec".

## Byte-level reference: gaps-signature-script.py

A deliberately broken script lives at `fixtures/gaps-signature-script.py`. It is not an expected output of `skill-signed-handoff`; it is a lint-regression fixture. Running `handoff_lint.py fixtures/gaps-signature-script.py` must report `passed: false` with at least the following fails:

- Rule B (no `--verify` token)
- Rule C (no sha256 — uses md5)
- Rule D (empty SIGNED_FIELDS list)
- Rule E (exit codes 2 and 3 unreachable)
- Rule F (no canonical sort)

## Why this fixture matters

- Proves strict-stop discipline (BP-028) — the sub-skill refuses to invent a field list the spec did not declare.
- Proves lint-coverage of the common drift modes — a script that SAYS it signs but uses md5, or that only signs (never verifies), or that hashes an unsorted dict, is caught before it ships.
- Proves early-exit — the skill stops at Step 4 of its own procedure rather than running through a degraded path that would produce a useless signature script.
