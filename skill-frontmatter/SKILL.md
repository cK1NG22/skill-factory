---
meta-skill: true
name: skill-frontmatter
description: Generate compliant YAML frontmatter for a factory-authored skill from a validated spec. Use when "generate frontmatter", "write the frontmatter block", "lint frontmatter", "check this frontmatter", "skill-frontmatter <workspace>", or when the skill-factory driver invokes this in Phase 4. Do NOT use for editing SKILL.md body content — this skill writes ONLY the YAML frontmatter block between the opening and closing `---` lines.
argument-hint: "<phases-dir-or-input-md-path>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-frontmatter

**Read ONLY your `phases/01-skill-frontmatter/input.md`** (per BP-033). The driver has distilled the specific BP file paths and spec excerpt you need into `input.md` — it will list exactly which `patterns/bp-NNN-*.md` files to read (if any). Do NOT open the `patterns/` directory directly. Do NOT open the full spec file directly; the relevant excerpts are already in your input pack.

The one thing this skill produces: a YAML frontmatter block that passes `scripts/frontmatter_lint.py` against `references/frontmatter-rules.md`.

## What this skill does NOT do

- Does NOT author SKILL.md body content (that is downstream sub-skills' jobs).
- Does NOT invent facts about the skill beyond what the spec excerpt provides.
- Does NOT write files outside its phase workspace directory.
- Does NOT invoke other sub-skills.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 4. Reads from and writes to the driver's session workspace:

**Reads:**
- `phases/01-skill-frontmatter/input.md` — the driver-materialized context pack (spec excerpt + trait verdicts + list of BP file paths).

**Writes (to `phases/01-skill-frontmatter/`):**
- `output.yaml` — the raw frontmatter block, parseable (between `---` delimiters).
- `output.md` — human-readable version showing the frontmatter with a rationale paragraph for each major decision (name construction, tool selection, trigger-phrase order).
- `notes.md` — `BLOCKER:` lines if any, otherwise short observations.

### Standalone (manual invocation)

```
/skill-frontmatter ~/Claude/skill-factory-sessions/<session>/phases/01-skill-frontmatter/
```

or

```
/skill-frontmatter ~/Claude/skill-factory-sessions/<session>/phases/01-skill-frontmatter/input.md
```

Same procedure; reads the input pack, produces the three output files in the same directory.

## Procedure

Follow these steps in order. Do NOT skip or re-order.

### Step 1 — Load the input pack

Read `phases/01-skill-frontmatter/input.md` (or the file passed as the argument). The pack contains, at minimum:
- **Task** — a one-line statement.
- **Spec excerpt** — Company, Skill slug, One-line description, Trigger phrases, Inputs, Outputs, Happy-path walkthrough.
- **Classified traits** — the 5 trait verdicts from Phase 2.
- **BPs to enforce** — absolute paths to `patterns/bp-NNN-*.md` files you must consult.
- **Output locations** — where to write `output.yaml`, `output.md`, `notes.md`.

### Step 2 — Load the rules contract

Read `references/frontmatter-rules.md` (sibling to this SKILL.md in the skill directory). This is the authoritative source for Rules 1–5. The lint script implements exactly these rules.

### Step 3 — Read the listed BP files

For each `patterns/bp-NNN-*.md` path listed under "BPs to enforce" in the input pack, read the file. Understand the rule. Do NOT read BP files not listed in the pack — the driver selected the relevant ones based on the spec.

### Step 4 — Construct `name`

- `name = <skill-slug>` taken directly from the spec excerpt. The company prefix is NOT prepended; per-client repos at `~/Projects/<company>-claude-skills/` provide the namespace.
- Verify the slug against Rule 1: `^[a-z][a-z0-9-]{1,63}$`, not in reserved-names set.
- If the slug exceeds 64 chars, write `BLOCKER: slug '<slug>' exceeds 64 char limit (len=N); upstream spec must shorten Skill slug` to `notes.md` and STOP.

### Step 5 — Construct `description`

Structure:
```
<one-line action-verb summary>. Use when <'phrase1'>, <'phrase2'>, <'phrase3'>, ..., <'phrase7'>. Do NOT use for <negative case>.
```

Rules:
- Start with the spec's `One-line description` verbatim (it already passed spec-validator's third-person action-verb check).
- Then `. Use when ` followed by each trigger phrase from the spec's `Trigger phrases` section, quoted, comma-separated. Include all the spec's phrases if 5–10; truncate to 10 if the spec has more.
- End with a `Do NOT use for <X>` clause derived from the spec's `Anti-goals` section if present, or from obvious negative cases in the Inputs section ("use /docx for generic markdown→docx conversion" is the canonical pattern for adapter skills).
- Total length must be 80 ≤ N ≤ 1024 chars.

### Step 6 — Construct `allowed-tools`

Infer from the spec's Happy-path walkthrough:

| Walkthrough contains | Add tool |
|---|---|
| reads a file from disk | `Read` |
| writes output to disk | `Write` |
| invokes `/<skill-name>` | `Agent` |
| runs a shell command | `Bash` |
| asks the user a question | `AskUserQuestion` |
| searches files by pattern | `Glob`, `Grep` |
| fetches a URL | `WebFetch` |

Also: if the trait verdict has `has_hitl: true`, include `AskUserQuestion`. If `invokes_skills: true`, include `Agent`.

Do NOT list tools the walkthrough does not use.

### Step 7 — Construct `argument-hint` (optional)

If the spec's Inputs section names a single primary argument (e.g., "A path to a .md file"), include:
```yaml
argument-hint: "<path-to-markdown-file>"
```
Omit this key if the skill takes no arguments or multiple unrelated ones.

### Step 8 — Assemble the draft frontmatter block

Write the block to `output.yaml`:
```yaml
---
name: <value-from-step-4>
description: >-
  <value-from-step-5>
argument-hint: "<value-from-step-7-if-applicable>"
allowed-tools:
  - <tool>
  - <tool>
---
```

### Step 9 — Self-lint

Run:
```bash
python3 scripts/frontmatter_lint.py output.yaml
```

The script returns JSON with `passed: true/false` plus `fails`, `warns`, `info` arrays. See `references/frontmatter-rules.md` for what each rule checks.

**If `passed: true`:** write `output.md` with the frontmatter plus a short rationale paragraph for each non-obvious decision (why this tool, why this trigger order). Write `notes.md` with any lint `warns` repeated as informational observations. STOP. Task complete.

**If `passed: false` (first attempt):** apply the fix suggested by each `fails` entry. Re-run steps 4–8 as needed. Re-run the lint.

**If `passed: false` (second attempt):** write `BLOCKER: frontmatter_lint failed twice; see fails[] for details` to `notes.md`. Do NOT write `output.yaml`. STOP. Let a human inspect per BP-028.

### Step 10 — Write output files

- `output.yaml` contains ONLY the frontmatter block (including the opening and closing `---`).
- `output.md` contains the frontmatter block followed by a `## Rationale` section explaining each major decision.
- `notes.md` contains either blocker lines or informational observations about lint warnings.

## Self-test

The skill ships with two fixtures under `fixtures/`:

**Passing fixture:**
```
/skill-frontmatter fixtures/passing-input.md
```
Expected: `output.yaml` lints clean (`passed: true`, 0 fails, 0 warns), matches `fixtures/expected-pass-output.yaml`.

**Gaps fixture:**
```
/skill-frontmatter fixtures/gaps-input.md
```
Expected: `notes.md` contains a `BLOCKER:` line; no `output.yaml` produced.

## Patterns enforced

- **BP-001** — description contains explicit trigger phrases
- **BP-002** — description is "pushy" (named triggers, negative clause)
- **BP-003** — name format (regex, length, reserved words)
- **BP-004** — description ≤1024 chars
- **BP-005** — allowed-tools declared
- **BP-028** — `BLOCKER:` convention when self-lint fails twice
- **BP-033** — read only `input.md`, never open `patterns/` directly

## What to do if you're stuck

- **`input.md` missing** → write `BLOCKER: input.md not found at <path>` to `notes.md`. Do not guess.
- **Spec excerpt in `input.md` is missing a required section** (Company / Skill slug / Description / Trigger phrases) → write `BLOCKER: spec excerpt incomplete — missing <section>` to `notes.md`. This means the driver's pack-building step has a bug; do not attempt to invent values.
- **Combined name exceeds 64 chars** → `BLOCKER:` with the actual length. Spec must shorten the slug.
- **Trigger phrases fewer than 5** → warn in `notes.md`, continue. The spec-validator's contract allows 5–10 but Rule 3 accepts 3 as the hard minimum.
- **Classified traits contradict the walkthrough** (e.g., `invokes_skills: true` but walkthrough names no `/<skill>`) → use the walkthrough as ground truth. Record the contradiction in `notes.md` as an informational observation; do not BLOCKER unless it prevents allowed-tools selection.

## Why this skill is strict

The frontmatter is the skill's only public interface to the dispatcher. A malformed `name:` breaks invocation. An under-triggered `description:` makes the skill un-discoverable. A missing `allowed-tools:` produces permission prompts mid-flow. Every downstream sub-skill assumes the frontmatter is correct; a bug here silently poisons the pipeline. Strict self-lint with forced BLOCKER on two failures is cheaper than silent production regressions.
