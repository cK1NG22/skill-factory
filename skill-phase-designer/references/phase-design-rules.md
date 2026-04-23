# Phase-design rules — authoritative contract

Six rules govern the `## Procedure` section of a factory-authored skill. Rules 1–3 are universal when `has_phases` fires. Rules 4–6 are conditional on `has_hitl`.

The deterministic lint at `scripts/phase_lint.py` checks each rule mechanically. When this document and the lint script diverge, **the lint is authoritative** — update this document to match the lint, not the other way around (factory convention per the skill-frontmatter precedent).

---

## Rule 1 — Steps are numbered and sequential (BP-010)

Each step in the Procedure section must begin with a `### Step N — <label>` heading. The step numbers must be:

- Sequential: 1, 2, 3, … with no gaps.
- Monotonic: no "Step 2" before "Step 1".
- Dense: no skipped numbers (no "Step 3" followed by "Step 5").

**Why:** Out-of-order or gapped numbering signals either an edit mid-revision or a conceptual bug. A well-formed Procedure section reads top-to-bottom with no surprises.

**Correct:**
```markdown
### Step 1 — Load the input
...
### Step 2 — Validate
...
### Step 3 — Write output
```

**Incorrect:**
```markdown
### Step 1 — Load
### Step 3 — Write        ← gap
### Step 2 — Validate     ← out of order
```

---

## Rule 2 — Each step starts with an imperative verb

The first word of each step's body (after the `### Step N — <label>` heading) must be an imperative verb from the canonical list below, or begin with a control keyword (`If`, `For`, `While`, `Else`).

**Canonical imperative verbs:** Read, Write, Parse, Invoke, Check, Validate, Ensure, Add, Run, Print, Fetch, Consult, Assemble, Present, Prompt, Ask, Wait, Do, Set, Return, Exit, Create, Delete, Compute, Evaluate, Emit, Announce, Stop, Continue, Capture, Strip, Walk, Generate, Build, Render, Process, Extract, Verify, Save, Load, Open, Close, Move, Copy, Apply, Try, Catch, Raise, Log, Scan, Lint, Output, Materialize, Spawn, Compose, Draft, Signal, Gate, Collect, Pick, Select, Test, Record, Register, Install, Uninstall, Mount, Unmount, Push, Pop, Append, Prepend, Insert, Remove, Replace, Rename, Retry, Skip, Resume, Classify, Tag, Mark, Flag, Unify, Merge, Split, Join, Group, Sort, Normalize, Resolve, Reject, Accept, Confirm, Use, Update, Upload, Download, Hand, Answer, Respond, Reply, Notify, Warn, Report, Surface, Escalate, Abort, Fail, Succeed, Begin, End, Start, Finish, Note, Remember, Forget, Clear, Reset, Prepare, Clean.

Control keywords acceptable as the first word: `If`, `For`, `While`, `Else`, `When`, `After`, `Before`.

**Correct:**
- `Read the input file from the path argument.`
- `For each topic in the agenda: ask the user to confirm.`

**Incorrect:**
- `The input file is read from the path argument.` ← passive
- `We should read the input file.` ← weak auxiliary
- `You might want to read the file.` ← hedged

---

## Rule 3 — No weak / passive voice

The procedure text must not contain any of these phrases (case-insensitive):

- "should be"
- "will be"
- "we should"
- "you should"
- "it should"
- "the user should"
- "we will"
- "might want to"
- "try to"
- "attempt to"
- "consider <verb>ing"
- "it is recommended"
- "the system will"

Weak voice hedges behavior. In a SKILL.md Procedure, the agent needs an instruction, not a suggestion.

**Correct:** `Validate the four required sections. Fail fast with a specific error if any is missing.`

**Incorrect:** `The four required sections should be validated and we might want to fail with an error.`

---

## Rule 4 — At least one hard gate (BP-012, only if `has_hitl: true`)

When `has_hitl` fires, the Procedure must contain at least one explicit "Do NOT proceed until …" or "Do NOT proceed to <step> until …" gate. The gate:

- Uses the literal phrase "Do NOT proceed" (case: "NOT" in caps per factory convention).
- Names the precondition that must be satisfied.
- Sits immediately before the irreversible or expensive step it guards.

**Why:** Without an explicit gate, the agent will barrel through a checkpoint. A user who turns their back for a moment returns to find downstream actions already taken.

**Correct:** `Do NOT proceed to Step 5 until the user confirms the chosen solution from Step 4.`

**Incorrect:** `Make sure the user is OK with the chosen solution before moving on.`

---

## Rule 5 — Questions are numbered or use `AskUserQuestion` (BP-015, only if `has_hitl: true`)

Every user-facing question in the Procedure must either:

- Be numbered as part of a numbered list (`1. …?`, `2. …?`, …), OR
- Be invoked via `AskUserQuestion(...)` with explicit options.

A free-text line that ends in a `?` but is NOT numbered or inside `AskUserQuestion(...)` is a violation.

**Correct:**
```
Answer all four before proceeding:
1. What is the target audience?
2. What is the deadline?
3. What is the success metric?
4. Which format (deck, doc, memo)?
```

Or:
```
Invoke AskUserQuestion with options: ["deck", "doc", "memo"].
```

**Incorrect:**
```
What is the target audience? And what is the deadline? And what format should we use?
```

---

## Rule 6 — At most 4 inline questions (BP-016, only if `has_hitl: true`)

Count every `?` in the Procedure text (excluding `?` inside fenced code blocks or quoted strings). If the count is more than 4, the overflow must be moved to a `references/scoping-questions.md` file, with the Procedure instead saying:

> Ask the remaining questions from `references/scoping-questions.md`.

**Why:** Every inline question bloats the traffic-director SKILL.md. Past a small threshold, the questions belong in a reference the skill can consult on demand.

**Correct:** ≤4 inline questions, each a single short sentence.

**Incorrect:** 7 questions inlined with multi-sentence explanations.

---

## Worked composed example — acme-board-memo (has_phases + invokes_skills, no HITL)

Rules 1, 2, 3 apply. Rules 4, 5, 6 do not (HITL is off).

```markdown
## Procedure

### Step 1 — Load the input markdown
Read the input `.md` file from the path argument. Fail fast with exit code 1 if the path does not exist.

### Step 2 — Parse front-matter
Parse the optional YAML front-matter block. Capture `meeting_date` and `author` if present; leave each field empty otherwise.

### Step 3 — Validate required sections
Validate that the four required top-level sections (`# Title`, `## Summary`, `## Discussion`, `## Recommendation`) are present. Fail fast with a specific error naming the missing section if any is absent.

### Step 4 — Invoke `/docx`
Invoke the `/docx` skill to construct the document. Populate the Acme cover-page template with the title, meeting date (or `TBD`), and author (or `TBD`).

### Step 5 — Write the output
Write the finished `.docx` to `~/Claude/acme-board-memo/<input-stem>.docx`. Ensure the output directory exists; create it if missing.

### Step 6 — Print the output path
Print the absolute output path to stdout.
```

Lint verdict on this block: `passed: true`, 0 fails, 0 warns, 6 steps.
