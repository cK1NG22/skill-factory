# Input pack — skill-references-scaffolder (passing, references-only)

## Task
Verify the target skill's `references/` folder and SKILL.md citations pass lint.

## Spec excerpt

### Company
acme

### Skill slug
strategy-coach

### References list
- `scoping-questions.md` — full intake checklist to ask the client during Phase 1.
- `strategy-overview.md` — per-phase theory map the agent loads before diagnosis.
- `anti-patterns.md` — canonical failure-mode catalog surfaced during review.

### Happy-path walkthrough
1. Read the scoping-questions reference and ask the first four.
2. Read the strategy-overview reference before diagnosing.
3. Read the anti-patterns reference before the review step.

## Classified traits
```
has_references: true
has_phases: false
has_hitl: false
is_scheduled: false
invokes_skills: false
```

## BPs to enforce
- {{REPO_ROOT}}/patterns/bp-007-references-loaded-on-demand.md
- {{REPO_ROOT}}/patterns/bp-008-references-one-level-deep.md

## Target skill directory
{{REPO_ROOT}}/skill-references-scaffolder/fixtures/passing-skill

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the scaffolder's plan + lint verdict.
- `notes.md` — `BLOCKER:` lines or informational observations.
