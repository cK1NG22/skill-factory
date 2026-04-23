# Expected output — passing-no-hitl-input.md

When `skill-phase-designer` runs against `fixtures/passing-no-hitl-input.md`, it should produce an `output.md` whose Procedure section passes `phase_lint.py` without `--hitl`:

```json
{"passed": true, "fails": []}
```

## Acceptance criteria

1. `output.md` exists and opens with `## Procedure`.
2. Exactly **10 `### Step N — <label>` headings**, numbered 1..10 sequentially.
3. Each step body's first word is an imperative verb from the canonical list (Read, Parse, Validate, Invoke, Insert, Render, Add, Ensure, Write, Print).
4. No weak-voice phrases anywhere in `output.md` ("should be", "we should", "might want to", etc.).
5. Running `phase_lint.py output.md` with NO `--hitl` flag returns `passed: true`.
6. `notes.md` contains no `BLOCKER:` line. It may include informational observations about the 10 steps and the `/docx` invocation.

## Rationale section is optional

Unlike `skill-frontmatter`, this sub-skill produces a single drop-in artifact (the Procedure section). A `## Rationale` section in `output.md` is permitted but not required — the rules contract does not assess it.

## What counts as BP-010 satisfaction

The acme walkthrough reads only one file (the input `.md`); the other steps build on the invocation result in memory. No redundant reads across steps exist, so BP-010 has nothing to enforce. That is a valid pass.
