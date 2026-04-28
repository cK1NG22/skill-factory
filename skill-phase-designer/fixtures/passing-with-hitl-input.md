# Input pack — skill-phase-designer

## Task
Draft a `## Procedure` section for the target skill's SKILL.md from the spec's Happy-path walkthrough. Write `output.md` and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
board-prep

### One-line description
Prepares a board meeting packet through a six-step interactive workflow.

### Inputs
A path to a YAML agenda file describing meeting topics.

### Outputs
A `.docx` file at `~/Claude/board-prep/<meeting-date>-packet.docx`.

### Happy-path walkthrough
1. Read the agenda YAML. Ask the user to confirm each topic before proceeding.
2. For each topic, prompt the user for talking points. Wait for the user before moving on.
3. Fetch prior-period financials from the reference lookup table.
4. Consult the scoring rubric in the reference framework to rank risks.
5. Assemble the packet using `/docx` to render the final document.
6. Present a preview and ask the user to confirm before writing the output.

### Failure modes
- **Agenda YAML malformed** → fail-fast with the offending line number.
- **`/docx` unavailable** → write `BLOCKER:` per BP-028.
- **User abandons at any hard gate** → exit cleanly, preserve partial work.

### Existing skills to reuse
- `/docx` — renders the final packet document.

## Classified traits
```
has_references: true
has_phases: true
has_hitl: true
is_scheduled: false
invokes_skills: true
  - /docx
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-010-apply-once-carry-forward.md
- {{REPO_ROOT}}/patterns/bp-011-announce-phase-transitions.md
- {{REPO_ROOT}}/patterns/bp-012-hard-gates.md
- {{REPO_ROOT}}/patterns/bp-013-ask-user-first.md
- {{REPO_ROOT}}/patterns/bp-015-number-questions.md
- {{REPO_ROOT}}/patterns/bp-016-inline-question-rule.md

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the draft `## Procedure` section ready to paste into the target SKILL.md.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
