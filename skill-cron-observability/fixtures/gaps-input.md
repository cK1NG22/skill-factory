# Input pack — skill-cron-observability

## Task
Generate an instrumentation snippet that wires the BP-022 observability contract into the target cron skill's scripts. Write `instrumentation-snippet.md`, `output.md`, and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
nightly-backup

### One-line description
Backs up the engineering wiki nightly.

### Inputs
None.

### Outputs
A backup file somewhere on disk.

### Scheduling
(The spec author forgot to declare cron frequency and artifact extension here.)

### Happy-path walkthrough
1. Export the wiki.
2. Write a backup file.

### Failure modes
- **Wiki unreachable** → fail-fast.

### Existing skills to reuse
None

## Classified traits
```
has_references: false
has_phases: false
has_hitl: false
is_scheduled: true
invokes_skills: false
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-022-cron-observability.md

## Output locations
Write into the directory containing this `input.md`:
- `instrumentation-snippet.md` — the fenced Python snippet ready to paste.
- `output.md` — rationale wrapper.
- `notes.md` — `BLOCKER:` lines if any.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
