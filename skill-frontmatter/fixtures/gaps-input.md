# Input pack — skill-frontmatter

## Task
Generate compliant YAML frontmatter for a factory-authored skill.

## Spec excerpt

### Company
verylongcompanyname-ltd-international

### Skill slug
customer-onboarding-pipeline-with-all-the-features-included-and-more-comprehensive

### One-line description
Onboards customers.

### Trigger phrases
- "onboard"
- "run onboarding"

### Inputs
Stuff.

### Outputs
A checklist.

### Happy-path walkthrough
Process the onboarding.

## Classified traits
```
has_references: false
has_phases: false
has_hitl: false
is_scheduled: false
invokes_skills: false
```

## BPs to enforce
- /Users/carterking/Projects/skill-factory/patterns/bp-001-trigger-phrases.md
- /Users/carterking/Projects/skill-factory/patterns/bp-003-name-rules.md
- /Users/carterking/Projects/skill-factory/patterns/bp-004-description-length.md
- /Users/carterking/Projects/skill-factory/patterns/bp-005-allowed-tools.md

## Output locations
Write into the directory containing this `input.md`:
- `output.yaml`
- `output.md`
- `notes.md`
