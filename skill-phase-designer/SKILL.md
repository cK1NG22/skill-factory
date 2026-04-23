---
name: skill-phase-designer
description: Design a SKILL.md Procedure section for a phased skill from a validated spec. Use when "design the procedure", "lay out the phases", "generate procedure steps", "draft the walkthrough steps", "skill-phase-designer <workspace>", or when the skill-factory driver invokes this in Phase 4 because has_phases fires. Do NOT use for writing the SKILL.md frontmatter (use skill-frontmatter) or for wiring references (use skill-references-scaffolder).
argument-hint: "<phases-dir-or-input-md-path>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-phase-designer

**Read ONLY your `phases/02-skill-phase-designer/input.md`** (per BP-033). The driver has distilled the spec's Happy-path walkthrough, the relevant traits (`has_phases`, `has_hitl`, `invokes_skills`), and the specific BP file paths into `input.md`. Do NOT open the `patterns/` directory directly. Do NOT open the full spec file directly.

The one thing this skill produces: a `## Procedure` section for the target skill's SKILL.md that passes `scripts/phase_lint.py` against `references/phase-design-rules.md`.

## What this skill does NOT do

- Does NOT author the SKILL.md frontmatter (that is `skill-frontmatter`'s job).
- Does NOT decide the folder structure (that is `skill-references-scaffolder`'s job — BP-009).
- Does NOT compute signed handoffs (that is a future `skill-signed-handoff` — BP-024).
- Does NOT invent steps beyond what the spec's Happy-path walkthrough declares.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 4 when the `has_phases` trait fires.

**Reads:**
- `phases/02-skill-phase-designer/input.md` — the driver-materialized context pack.

**Writes (to `phases/02-skill-phase-designer/`):**
- `output.md` — a draft `## Procedure` section ready to paste into the target SKILL.md.
- `notes.md` — `BLOCKER:` lines if any, otherwise short observations.

### Standalone (manual)

```
/skill-phase-designer <path-to-input.md-or-its-parent-dir>
```

## Procedure

Follow these steps in order.

### Step 1 — Load the input pack

Read `input.md`. The pack contains:
- **Task** — a one-line statement.
- **Spec excerpt** — the Happy-path walkthrough (required), Inputs, Outputs, Failure modes, and, if `has_hitl` or `invokes_skills` fires, the relevant reuse/scoping sections.
- **Classified traits** — the 5 trait verdicts from Phase 2. Only `has_phases`, `has_hitl`, and `invokes_skills` matter for this sub-skill.
- **BPs to enforce** — absolute paths to the BP files. Always BP-010. If `has_hitl` fires, BP-011, BP-012, BP-013, BP-015, BP-016.
- **Output locations** — where to write `output.md` and `notes.md`.

If `has_phases` is not `true` in the pack, write `BLOCKER: skill-phase-designer invoked but has_phases is false — driver bug` to `notes.md` and STOP. This sub-skill must never run on non-phased skills.

### Step 2 — Load the rules contract

Read `references/phase-design-rules.md`. This is the authoritative source for Rules 1–6.

### Step 3 — Read the listed BP files

For each `patterns/bp-NNN-*.md` path listed under "BPs to enforce", read the file. Do NOT read BP files not listed.

### Step 4 — Extract the walkthrough steps

Parse the spec excerpt's `Happy-path walkthrough` (or `Workflow` / `Procedure`) section. Extract numbered items:
- If fewer than 3 numbered items, write `BLOCKER: walkthrough has <3 steps; has_phases should not have fired` to `notes.md` and STOP (this is also a driver bug per Phase 2 classification).
- If 3 or more, keep the full list. Each item will become one step in the output `## Procedure` section.

### Step 5 — Rewrite each step in imperative voice

For each walkthrough item, rewrite as:
- Starts with a single imperative verb (Read, Write, Parse, Invoke, Validate, Ensure, Print, Fetch, Assemble, Announce, Ask, Wait, Do, Run, Compute, Emit, Stop, Continue, …).
- One action per step. Split compound items into sub-steps only if the walkthrough itself was compound.
- Preserve file paths, skill names (`/docx`), and exit-code semantics verbatim.
- Remove passive voice ("the file is read" → "Read the file"). Remove weak auxiliaries ("we should", "you should", "it should be").

### Step 6 — Apply BP-010 (apply-once, carry forward)

Scan the steps for the same reference or input being re-read across multiple steps. If step N reads `X.md` and step N+2 also reads `X.md`, rewrite step N+2 to read step N's output instead. Document the intermediate output's expected location (e.g., `phase-N-output.md`). If no repeated reads exist, BP-010 has nothing to enforce — that is fine.

### Step 7 — Insert hard gates (only if `has_hitl: true`)

For each point in the walkthrough where the spec says the user confirms, chooses, or reviews before the next step, insert an explicit line:
```
Do NOT proceed until <condition>.
```
At minimum one `Do NOT proceed until …` line must appear anywhere in the procedure. Place gates AFTER the checkpoint, BEFORE the next irreversible or expensive step.

If `has_hitl: false`, skip this step entirely. No gates are needed.

### Step 8 — Format user questions (only if `has_hitl: true`)

If the spec's walkthrough inlines any user questions:
- Number each question (`1. … 2. … 3. …`) per BP-015.
- For choice-shaped questions (select one of N options), annotate with `use AskUserQuestion` in a parenthetical, per BP-015.
- Count total inline questions. If more than 4, move the overflow to a brief mention: "Ask the remaining questions from `references/scoping-questions.md`" per BP-016. Flag this in `notes.md` so the downstream `skill-references-scaffolder` knows to create that file.

If `has_hitl: false`, skip this step.

### Step 9 — Assemble the output

Write to `output.md`:
```markdown
## Procedure

### Step 1 — <short action label>
<imperative-voice body>

### Step 2 — <short action label>
<imperative-voice body>

...
```

Each step gets its own `### Step N — <label>` heading. The label is a short (3–7 word) action summary. The body is one or more sentences, all in imperative voice.

### Step 10 — Self-lint

Run the lint, passing the relevant trait flags extracted from Step 1's pack:

```bash
python3 scripts/phase_lint.py output.md [--hitl] [--invokes-skills]
```

Pass `--hitl` iff the pack's `Classified traits` block has `has_hitl: true`. Pass `--invokes-skills` iff it has `invokes_skills: true`. Both flags are boolean toggles; omit either or both when the corresponding trait is false. The lint returns JSON with `passed`, `fails`, `warns`, `info`.

**If `passed: true`:** write `notes.md` with any warnings as informational observations. STOP. Task complete.

**If `passed: false` (first attempt):** apply the fix suggested by each `fails` entry. Re-run steps 5–9 as needed. Re-run the lint.

**If `passed: false` (second attempt):** write `BLOCKER: phase_lint failed twice; see fails[] for details` to `notes.md`. Do NOT overwrite `output.md` with a broken version. STOP. Human inspects per BP-028.

## Self-test

The skill ships with three fixtures under `fixtures/`:

- `passing-no-hitl-input.md` — acme-board-memo-style pack (has_phases + invokes_skills, no HITL).
- `passing-with-hitl-input.md` — board-prep-style pack (has_phases + has_hitl + invokes_skills).
- `gaps-input.md` — walkthrough has only 2 numbered items; expected to BLOCKER at Step 4.

Each has a matching `expected-*.md` oracle describing acceptance.

## Patterns enforced

- **BP-010** — apply-once, carry forward (no redundant reads across steps).
- **BP-011** — announce phase transitions (when `has_hitl`).
- **BP-012** — hard gates with `Do NOT proceed until …` (when `has_hitl`).
- **BP-013** — ask user first, then suggest (when `has_hitl`).
- **BP-015** — number questions, use `AskUserQuestion` for choices (when `has_hitl`).
- **BP-016** — inline-question rule, ≤4 questions (when `has_hitl`).
- **BP-028** — `BLOCKER:` convention when self-lint fails twice or input preconditions violated.
- **BP-033** — read only `input.md`, never open `patterns/` directly.

## What to do if you're stuck

- **`input.md` missing** → write `BLOCKER: input.md not found at <path>` to `notes.md`. Do not guess.
- **Walkthrough has <3 steps** → `BLOCKER: walkthrough has <3 steps; has_phases should not have fired`. This is a driver bug — surface it.
- **`has_phases: false` in the pack** → `BLOCKER: skill-phase-designer invoked but has_phases is false — driver bug`. This sub-skill must not run on non-phased skills.
- **Spec walkthrough contradicts the HITL trait verdict** (walkthrough has questions but `has_hitl: false`, or vice versa) — use the walkthrough as ground truth. Record the contradiction as an informational observation; do not BLOCKER unless the lint fails.
- **Two lint failures in a row** → `BLOCKER:`. Let a human inspect.

## Why this skill is strict

The Procedure section is the runtime contract of a skill — the sequence the agent actually follows. Non-imperative voice produces hedged behavior; missing hard gates cause skipped checkpoints; redundant reads inflate context cost. The deterministic lint catches structural problems that an eyeball review misses (step 4 was skipped; step 7 uses passive voice; a question is not numbered). Strict self-lint with forced BLOCKER on two failures is cheaper than a skill that silently behaves wrong in production.
