# Expected output — passing-with-hitl-input.md

When `skill-phase-designer` runs against `fixtures/passing-with-hitl-input.md`, it should produce an `output.md` whose Procedure section passes `phase_lint.py --hitl --invokes-skills`:

```json
{"passed": true, "fails": []}
```

## Acceptance criteria

1. `output.md` exists and opens with `## Procedure`.
2. At least **6 `### Step N — <label>` headings**, numbered sequentially 1..N. (The sub-skill is permitted to split interactive steps into sub-steps; e.g., "ask the user to confirm each topic" may become its own step. Expect 6–10 total.)
3. Each step body's first word is an imperative verb from the canonical list.
4. No weak-voice phrases anywhere.
5. At least one explicit `Do NOT proceed until …` hard gate somewhere in the Procedure (Rule 4 / BP-012).
6. Any user-facing question that ends in `?` is either numbered (`1. …?`) or preceded / followed within 3 lines by an `AskUserQuestion` mention (Rule 5 / BP-015).
7. No more than 4 inline `?` characters outside fenced code and quoted strings (Rule 6 / BP-016). If more, warn (not fail) with "move overflow to references/scoping-questions.md".

## Notes the sub-skill is expected to emit

- Mention that BP-024 (signed handoffs) is a future `skill-signed-handoff` concern since `invokes_skills` fires — this appears as an `info` line from the lint, not a `BLOCKER`.
- Flag the `/docx` invocation at Step 5 (or wherever it lands) as the trust boundary.

## What counts as BP-012 satisfaction

Hard gate examples that satisfy Rule 4:
- "Do NOT proceed to Step 2 until the user has confirmed all agenda topics."
- "Do NOT proceed to writing the output until the user confirms the preview."

A single gate anywhere is sufficient; more is better. The user-reversibility boundary (any step after which content is irreversibly written or sent) is the right place to put one.
