# Input pack — skill-frontmatter

## Task
Generate compliant YAML frontmatter for a factory-authored skill. Write `output.yaml`, `output.md`, and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
board-memo

### One-line description
Generates a formatted .docx board memo from a markdown outline using Acme's cover page and section styling.

### Trigger phrases
- "generate board memo"
- "board memo from this"
- "make a board memo"
- "turn this into a board memo"
- "render as board memo"
- "acme board memo"
- "board memo docx"

### Inputs
A path to a `.md` file containing a board memo outline with required sections (Title, Summary, Discussion, Recommendation).

### Outputs
A `.docx` file at `~/Claude/board-memo/<input-stem>.docx`.

### Happy-path walkthrough
1. Read the input `.md` file from the path argument.
2. Parse optional YAML front-matter for meeting_date and author.
3. Validate the four required sections.
4. Invoke the `/docx` skill to build the document.
5. Write the output to `~/Claude/board-memo/<input-stem>.docx`.
6. Print the absolute output path to stdout.

### Anti-goals
- Do NOT include content not present in the source markdown.
- Do NOT modify the input file.

## Classified traits
```
has_references: false
has_phases: true
has_hitl: false
is_scheduled: false
invokes_skills: true
  - /docx
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-001-trigger-phrases.md
- {{REPO_ROOT}}/patterns/bp-002-pushy-description.md
- {{REPO_ROOT}}/patterns/bp-003-name-rules.md
- {{REPO_ROOT}}/patterns/bp-004-description-length.md
- {{REPO_ROOT}}/patterns/bp-005-allowed-tools.md

## Output locations
Write into the directory containing this `input.md`:
- `output.yaml` — the raw frontmatter block (between `---` delimiters), parseable.
- `output.md` — frontmatter + a `## Rationale` section explaining name/tools/trigger-order decisions.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly — the BP files you need are the ones listed above.
