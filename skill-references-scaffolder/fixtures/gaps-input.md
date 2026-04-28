# Input pack — skill-references-scaffolder (gaps)

## Task
Surface every rule violation in the target skill and refuse to silently fix them.

## Spec excerpt

### Company
acme

### Skill slug
broken

### References list
- `scoping-questions.md` — intake list.
- `anti-patterns.md` — failure-mode catalog (intentionally uncited in target SKILL.md).

### Happy-path walkthrough
1. Read scoping questions.
2. (Anti-patterns should also be read — intentionally missing.)

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
{{REPO_ROOT}}/skill-references-scaffolder/fixtures/gaps-skill

## Output locations
Write into the directory containing this `input.md`:
- `output.md` — the scaffolder's plan + lint verdict.
- `notes.md` — `BLOCKER:` lines or informational observations.
