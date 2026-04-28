# Input pack — skill-signed-handoff

## Task
Stamp a `<slug>_signature.py` script for the upstream skill's terminal phase, signing the argument-bearing fields declared in the spec. Write `output-signature-template.py` and `notes.md` into the same directory as this `input.md`.

## Spec excerpt

### Company
acme

### Skill slug
acme-deck

### One-line description
Builds a .pptx deck from a 411-case handoff spec.

### Pipeline composition
- **Upstream:** `/acme-case` writes the deck spec in its terminal phase (phase-6).
- **Downstream:** `/acme-deck` (this skill) reads the spec in its entry phase (phase-1) and must verify the signature before consuming any fields.

### Argument-bearing fields
The handoff contract signs the following fields of the deck spec:
- `argument_flow`
- `leadlines`
- `recommendation`

### Happy-path walkthrough
1. Upstream terminal phase runs `scripts/acme-deck_signature.py --sign spec.json signature.txt`.
2. Downstream entry phase runs `scripts/acme-deck_signature.py --verify spec.json signature.txt`.
3. On verify-success (exit 0), downstream consumes the signed fields.

### Failure modes
- **Signed field missing from payload** → exit 1.
- **Digest mismatch** → exit 2.
- **I/O error (payload or signature file unreadable)** → exit 3.

### Existing skills to reuse
- `/acme-case` — upstream producer of the deck spec.

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
- {{REPO_ROOT}}/patterns/bp-024-signed-handoffs.md
- {{REPO_ROOT}}/patterns/meta/bp-028-blocker-convention.md
- {{REPO_ROOT}}/patterns/meta/bp-033-driver-context-packs.md

## Output locations
Write into the directory containing this `input.md`:
- `output-signature-template.py` — the stamped signature script ready to drop into the target skill's `scripts/` directory.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.

Do NOT read any files not listed above. Do NOT open `patterns/` directly.
