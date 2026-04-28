# Input pack — skill-references-scaffolder (passing, parallel folders)

## Task
Verify the target skill's parallel-folder layout (`phases/` + `references/`) passes lint.

## Spec excerpt

### Company
acme

### Skill slug
strategy-coach-phased

### References list
- `scoping-questions.md` — full intake checklist.
- `frameworks-map.md` — per-problem framework map.
- `anti-patterns.md` — canonical failure-mode catalog.

### Phases
- 01-intake
- 02-diagnose

### Happy-path walkthrough
1. Phase 01 — read scoping questions, ask the first four.
2. Phase 02 — read frameworks-map and anti-patterns, produce diagnosis.

## Classified traits
```
has_references: true
has_phases: true
has_hitl: false
is_scheduled: false
invokes_skills: false
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-007-references-loaded-on-demand.md
- {{REPO_ROOT}}/patterns/bp-008-references-one-level-deep.md
- {{REPO_ROOT}}/patterns/bp-009-parallel-folders.md

## Target skill directory
{{REPO_ROOT}}/skill-references-scaffolder/fixtures/passing-with-phases-skill

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the scaffolder's plan + lint verdict.
- `notes.md` — `BLOCKER:` lines or informational observations.
