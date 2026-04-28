# Input pack — skill-phase-designer

## Task
Draft a `## Procedure` section for the target skill's SKILL.md from the spec's Happy-path walkthrough. Write `output.md` and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
dump-csv

### One-line description
Dumps a table to csv.

### Inputs
A database table name.

### Outputs
A `.csv` file at `~/Claude/dump-csv/<table>.csv`.

### Happy-path walkthrough
1. Connect to the database.
2. Write rows to the csv file.

### Failure modes
- **Database unreachable** → fail-fast with the connection error.

### Existing skills to reuse
None

## Classified traits
```
has_references: false
has_phases: true
has_hitl: false
is_scheduled: false
invokes_skills: false
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-010-apply-once-carry-forward.md

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the draft `## Procedure` section ready to paste into the target SKILL.md.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
