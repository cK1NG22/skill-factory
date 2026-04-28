# Input pack — skill-phase-designer

## Task
Draft a `## Procedure` section for the target skill's SKILL.md from the spec's Happy-path walkthrough. Write `output.md` and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
board-memo

### One-line description
Generates a formatted .docx board memo from a markdown outline using Acme's cover page and section styling.

### Inputs
A path to a `.md` file containing a board memo outline with four required top-level sections (Title, Summary, Discussion, Recommendation). An optional YAML front-matter block may supply `meeting_date` and `author`.

### Outputs
A `.docx` file at `~/Claude/acme-board-memo/<input-stem>.docx`.

### Happy-path walkthrough
1. Read the input `.md` file from the path argument. Fail fast with exit code 1 if the path does not exist.
2. Parse the optional YAML front-matter block. Capture `meeting_date` and `author` if present. Leave each field empty if the block is absent or the key is missing.
3. Validate that all four required top-level sections are present. Fail fast with a specific error naming the missing section if any is absent.
4. Invoke the `/docx` skill to construct a new document. Populate the Acme cover-page template with the title, meeting date (or `TBD`), and author (or `TBD`).
5. Insert an auto-generated table of contents on the page immediately after the cover.
6. Render each of Summary, Discussion, and Recommendation under an H1 styled with Acme's `SectionHeader` paragraph style.
7. Add a repeating page footer reading "CONFIDENTIAL — BOARD EYES ONLY" on every page including the cover.
8. Ensure the output directory `~/Claude/acme-board-memo/` exists. Create it if missing.
9. Write the finished `.docx` to `~/Claude/acme-board-memo/<input-stem>.docx`.
10. Print the absolute output path to stdout.

### Failure modes
- **Input file missing or unreadable** → fail-fast with exit code 1.
- **Input is missing one or more required sections** → fail-fast with a specific error naming the missing section.
- **`/docx` skill unavailable** → write `BLOCKER: /docx skill not installed` to `notes.md` per BP-028 and exit.

### Existing skills to reuse
- `/docx` — existing ecosystem skill that handles all `.docx` writing.

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
- {{REPO_ROOT}}/patterns/bp-010-apply-once-carry-forward.md

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the draft `## Procedure` section ready to paste into the target SKILL.md.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
