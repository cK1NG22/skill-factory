# Input pack — skill-cron-observability

## Task
Generate an instrumentation snippet that wires the BP-022 observability contract into the target cron skill's scripts. Write `instrumentation-snippet.md`, `output.md`, and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
weekly-digest

### One-line description
Produces a weekly markdown digest of the team's engineering activity, scheduled every Friday at 4pm.

### Inputs
None — reads from a fixed git log window.

### Outputs
A `.md` file at `~/Claude/acme-weekly-digest/runs/<timestamp>/artifact.md`.

### Scheduling
- **Cron frequency:** `0 16 * * 5` (Fridays at 16:00 UTC)
- **Artifact extension:** `.md`

### Happy-path walkthrough
1. Read the last 7 days of git log from the configured repositories.
2. Render a markdown digest summarizing commits, authors, and files touched.
3. Write the digest artifact and observability records per BP-022.
4. Update the `latest.json` pointer at the skill root.

### Failure modes
- **Git log fetch fails** → record `success: false` in `result.json`; do not update `latest.json`.

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
- /Users/carterking/Projects/skill-factory/patterns/bp-022-cron-observability.md
- /Users/carterking/Projects/skill-factory/patterns/bp-021-output-home.md

## Output locations
Write into the directory containing this `input.md`:
- `instrumentation-snippet.md` — the fenced Python snippet ready to paste into the target skill's cron orchestration.
- `output.md` — rationale wrapper around the snippet.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
