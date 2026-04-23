# Expected output — passing-input.md

When `skill-frontmatter` runs against `fixtures/passing-input.md`, it should produce these three files.

## output.yaml (authoritative — diff against this)

The exact string content of `output.yaml`:

```yaml
---
name: acme-board-memo
description: >-
  Generates a formatted .docx board memo from a markdown outline using Acme's
  cover page and section styling. Use when "generate board memo",
  "board memo from this", "make a board memo", "turn this into a board memo",
  "render as board memo", "acme board memo", "board memo docx". Do NOT use
  for generic markdown-to-docx conversion (use /docx directly) or for
  non-board-meeting documents.
argument-hint: "<path-to-markdown-outline>"
allowed-tools:
  - Read
  - Write
  - Agent
---
```

Acceptance criteria for `output.yaml`:
- `scripts/frontmatter_lint.py output.yaml` returns `passed: true` with 0 fails and 0 warns.
- `name` is `acme-board-memo` (17 chars, passes BP-003 regex).
- `description` is between 80 and 1024 chars (approximately 460).
- Description contains at least 5 quoted trigger phrases with spaces.
- Description contains a `Do NOT use for` clause.
- `allowed-tools` includes `Read`, `Write`, `Agent` — Read for loading the input md, Write for the output path decision/stdout, Agent for invoking `/docx`.
- `allowed-tools` does NOT include `AskUserQuestion` (spec has `has_hitl: false`).
- `allowed-tools` does NOT include `Bash` (walkthrough does not run shell commands).

## output.md

Contains the `output.yaml` block followed by a `## Rationale` section. Example rationale:

```markdown
---
<same frontmatter block as output.yaml>
---

## Rationale

- **Name**: `<company>-<skill-slug>` = `acme-board-memo`. 17 chars, under the 64-char limit. Lowercase letters + hyphens only, passes BP-003.
- **Description length**: approximately 460 chars, within the 80–1024 BP-004 window.
- **Trigger phrases**: all 7 from the spec included verbatim. Order preserved from the spec (most specific first).
- **Negative clause**: `Do NOT use for generic markdown-to-docx conversion (use /docx directly)` — derived from the spec's Anti-goals and the composition-with-/docx pattern.
- **allowed-tools**: Read (loads the input md), Write (writes the output path to stdout and ensures the output directory exists), Agent (invokes `/docx` per the walkthrough's step 4). Traits say `invokes_skills: true`, which the walkthrough confirms. AskUserQuestion is NOT included because `has_hitl: false`.
- **argument-hint**: `<path-to-markdown-outline>` — the spec names a single primary file argument.
```

Wording of the rationale may vary; acceptance is structural (headings present, each major decision is explained).

## notes.md

Empty or informational only. No `BLOCKER:` lines expected.

## Acceptance criteria summary

1. Three files produced: `output.yaml`, `output.md`, `notes.md`.
2. `output.yaml` passes the deterministic lint.
3. `notes.md` contains no `BLOCKER:` line.
4. `output.md` contains both the frontmatter block and a rationale section.
