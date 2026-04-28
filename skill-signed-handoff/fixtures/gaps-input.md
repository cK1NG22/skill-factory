# Input pack — skill-signed-handoff (gaps fixture)

## Task
Stamp a `<slug>_signature.py` script for the upstream skill's terminal phase, signing the argument-bearing fields declared in the spec. Write `output-signature-template.py` and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
acme-orphan

### One-line description
Builds something from another skill's output, allegedly.

### Pipeline composition
- **Upstream:** `/acme-case` writes something in phase-6.
- **Downstream:** `/acme-orphan` reads it in phase-1.

### Argument-bearing fields
_(none declared — the spec author forgot to list them)_

### Happy-path walkthrough
1. Upstream terminal phase "signs" somehow.
2. Downstream entry phase "verifies" somehow.
3. Continue.

### Failure modes
- **Unclear** — spec has no signed-field contract.

### Existing skills to reuse
- `/acme-case` — upstream.

## Classified traits
```
has_references: false
has_phases: true
has_hitl: false
is_scheduled: false
invokes_skills: true
  - /acme-case
```

## BPs to enforce
- /Users/carterking/Projects/skill-factory/patterns/bp-024-signed-handoffs.md
- /Users/carterking/Projects/skill-factory/patterns/meta/bp-028-blocker-convention.md
- /Users/carterking/Projects/skill-factory/patterns/meta/bp-033-driver-context-packs.md

## Output locations
Write into the directory containing this `input.md`:
- `output-signature-template.py` — the stamped signature script (should NOT be produced here — spec is incomplete).
- `notes.md` — `BLOCKER:` lines expected.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
