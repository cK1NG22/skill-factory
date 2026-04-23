# Frontmatter rules — authoritative contract

Every skill the factory produces MUST have a frontmatter block that passes these rules. This file is the authoritative source for `skill-frontmatter`'s self-lint; `scripts/frontmatter_lint.py` implements these rules deterministically.

If a rule changes here, update `frontmatter_lint.py` in the same commit. Contract and checker must not drift.

---

## Required keys

Every frontmatter block MUST declare these four top-level keys, in this order (the order is stylistic but the lint accepts any order):

```yaml
---
name: <slug>
description: <string>
allowed-tools:
  - <tool>
---
```

Optional keys the lint allows:
- `argument-hint: <string>` — shown to the user as a hint for positional args.
- `model: <model-id>` — overrides the default model for this skill.

Any top-level key not in the allow-list (above + argument-hint + model) is flagged by the lint as an unknown-key warning. Unknown keys don't fail authoring, but the skill author should confirm the key is intentional.

---

## Rule 1 — Name format (BP-003)

- **Pattern:** `^[a-z][a-z0-9-]{1,63}$`
- **Length:** 2–64 characters inclusive.
- **Forbidden first char:** digit, hyphen, uppercase letter.
- **Forbidden anywhere:** uppercase letters, underscores, spaces, dots, special characters.
- **Reserved names** (blocked): `anthropic`, `claude`, `claude-code`, `default`.

**Correct:** `acme-onboarding`, `411-deck`, `skill-spec-validator`, `board-memo`
**Incorrect:** `Acme_Onboarding`, `claude-helper`, `My Skill`, `a` (too short), `-leading-hyphen`

**Why it matters:** runtime invocation uses the name as the slash command. Names with uppercase, underscores, or spaces cause silent invocation failures. See BP-003.

**Factory convention:** for factory-authored skills, the name is `<company>-<skill-slug>` where both halves follow the same regex. The factory prepends `<company>-` so the spec's `Skill slug` section should NOT include the company prefix.

---

## Rule 2 — Description length (BP-004)

- **Maximum length:** 1024 characters inclusive.
- **Minimum length:** 80 characters (a description shorter than 80 chars almost certainly omits trigger phrases or is too generic to match triggers reliably).
- **Measured how:** total character count of the rendered YAML string value, including any explicit trigger-phrase enumerations.

**Why it matters:** descriptions get silently truncated past 1024 chars. The trigger phrases at the END of an over-long description are dropped first, breaking skill discovery. See BP-004.

**Factory convention:** target 600–900 chars. This leaves headroom for trigger phrases (BP-001) plus a "Do NOT use for X" negative clause at the end.

---

## Rule 3 — Trigger phrases in description (BP-001 + BP-002)

- **Count:** the description MUST contain at least 3 distinct quoted trigger phrases.
- **Format:** each phrase in double-quotes or single-quotes, each representing something a user would literally type in chat.
- **Target:** 5–10 phrases is the factory-recommended range (matches what `/skill-spec-validator` collects in the spec's `## Trigger phrases` section).
- **Pushiness (BP-002):** the description must name at least one concrete trigger — a verb + object. Not just "handles documents" but "converts markdown to docx", "turns md into word doc".

**Lint signal:** the lint counts occurrences of `"..."` and `'...'` quoted substrings that contain a space. Fewer than 3 = fail.

**Why it matters:** Claude undertriggers skills when descriptions lack literal trigger phrases. The dispatcher's decision is made from the description alone. Past incident: `/411-refine` would not fire on "use after research" because the description said "Use when…" and the dispatcher needed the literal "use when" signal. See BP-001, BP-002.

**Factory convention:** description structure looks like:
```
<one-line action-verb summary>. Use when <'phrase1'>, <'phrase2'>, <'phrase3'>, … . Do NOT use for <negative case>.
```
This shape satisfies count, pushiness, and negative-case discipline in one template.

---

## Rule 4 — allowed-tools declared (BP-005)

- **Required:** frontmatter MUST include `allowed-tools:` as a YAML list.
- **Allowed values** (drawn from the Claude Code tool registry):
  - Read, Write, Edit
  - Bash
  - Glob, Grep
  - WebFetch, WebSearch
  - AskUserQuestion
  - Agent
  - TaskCreate, TaskUpdate, TaskList, TaskGet, TaskOutput, TaskStop
  - NotebookEdit
  - ExitPlanMode, EnterPlanMode
  - Any MCP tool with fully-qualified name.
- **Empty list** (`allowed-tools: []`) is allowed ONLY for pure-text skills that never touch tools. The lint warns in this case.

**Why it matters:** without `allowed-tools`, Claude Code prompts the user for permission on every tool use, breaking long workflows with interruptions. Pre-declaring authorizes at skill load time. See BP-005.

**Factory convention:** tool choice is inferred from the spec's Happy-path walkthrough:
- Walkthrough reads a file → add `Read`.
- Walkthrough writes output → add `Write`.
- Walkthrough invokes another skill → add `Agent`.
- Walkthrough runs shell commands → add `Bash`.
- Walkthrough asks the user questions → add `AskUserQuestion`.
- Spec has a `has_hitl` trait → include `AskUserQuestion`.

Do NOT list tools the walkthrough does not use. Over-declaration is a minor issue; under-declaration causes mid-flow prompts.

---

## Rule 5 — Negative-case clause (BP-002 extension)

- **Recommended:** description includes a "Do NOT use for X" clause naming at least one kind of task the skill should NOT be dispatched for.
- **Lint behavior:** soft — absence is a warning, not a failure. Presence helps the dispatcher reject near-misses and improves trigger precision.

**Why it matters:** the factory's trigger-evals (BP-019) include should-NOT-trigger near-miss queries. A description without a negative clause routinely false-fires on those and produces a noisy classifier. See BP-002, BP-019.

---

## The composed contract — worked example

For a spec with:
- Company: `acme`
- Skill slug: `board-memo`
- One-line description: `Generates a formatted .docx board memo from a markdown outline using Acme's cover page and section styling.`
- Trigger phrases: 7 verbatim phrases

The compliant frontmatter is:

```yaml
---
name: acme-board-memo
description: >-
  Generates a formatted .docx board memo from a markdown outline using Acme's
  cover page and section styling. Use when "generate board memo",
  "board memo from this", "make a board memo", "turn this into a board memo",
  "render as board memo", "acme board memo", "board memo docx". Do NOT use
  for generic markdown-to-docx conversion (use /docx directly for that) or
  for non-board-meeting documents.
argument-hint: "<path-to-markdown-outline>"
allowed-tools:
  - Read
  - Write
  - Agent
---
```

Breakdown:
- `name` = `<company>-<slug>` = 17 chars, passes Rule 1.
- `description` = ~460 chars, passes Rule 2 (under 1024, over 80).
- 7 quoted trigger phrases, passes Rule 3 (≥3; within factory-recommended 5–10).
- `Do NOT use for…` clause, passes Rule 5.
- `allowed-tools` = `[Read, Write, Agent]` — Read (loads the input md), Write (writes the docx output path decision), Agent (invokes `/docx`). Passes Rule 4.

---

## BLOCKER conditions

Per BP-028, emit `BLOCKER:` to `notes.md` and exit without writing `output.yaml` if:
- The spec excerpt in `input.md` is missing the Company, Skill slug, One-line description, or Trigger phrases section. (These are required by the spec-validator's contract — their absence means the input.md was built against an invalid spec, which is a driver bug, not a frontmatter-authoring problem.)
- The Skill slug is `> 40 chars` (combined with a `<company>-` prefix it would breach Rule 1's 64-char limit and forcing a truncation would silently corrupt the name).
- `scripts/frontmatter_lint.py` returns `fails: > 0` on the draft AND a second iteration also fails (skill attempts self-correction once; two consecutive failures = BLOCKER, let a human inspect).

Blockers are recoverable in the sense that fixing the upstream spec lets the pipeline re-run. They are NOT gaps to negotiate mid-flow.
