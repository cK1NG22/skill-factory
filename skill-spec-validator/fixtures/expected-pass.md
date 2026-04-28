# Expected output — passing-spec.md

When `skill-spec-validator` runs against `fixtures/passing-spec.md`, it should produce the following.

## output.yaml (authoritative — diff against this)

```yaml
status: pass
spec_path: {{REPO_ROOT}}/skill-spec-validator/fixtures/passing-spec.md
sections_found:
  - Company
  - Skill slug
  - One-line description
  - Trigger phrases
  - Inputs
  - Outputs
  - Happy-path walkthrough
  - Success signals
  - Failure modes
  - Existing skills to reuse
optional_present:
  - Edge cases
  - Anti-goals
ready_for_classify: true
```

## output.md (human-readable version — wording may vary slightly, content must match)

```markdown
# Spec validation report — passing-spec.md

**STATUS: pass** ✅

All 10 required sections present and satisfy the content contract. Ready to proceed to trait classification.

## Required sections (10/10 ✓)
- ✓ Company
- ✓ Skill slug
- ✓ One-line description
- ✓ Trigger phrases
- ✓ Inputs
- ✓ Outputs
- ✓ Happy-path walkthrough
- ✓ Success signals
- ✓ Failure modes
- ✓ Existing skills to reuse

## Optional sections present (2)
- Edge cases
- Anti-goals

## Next step
Feed this spec to `/skill-factory acme <spec-path>` to author the skill.
```

## notes.md

Empty (no blockers, no anomalies).

## Acceptance criteria

- `output.yaml` parses as valid YAML.
- Every key listed above is present.
- `status` is exactly the string `pass`.
- `sections_found` contains exactly 10 entries in the order from `references/spec-requirements.md` for determinism (Company, Skill slug, One-line description, Trigger phrases, Inputs, Outputs, Happy-path walkthrough, Success signals, Failure modes, Existing skills to reuse).
- `optional_present` contains exactly 2 entries: `Edge cases`, `Anti-goals`. Both match_patterns in `spec-requirements.md` hit against this fixture — the validator should recognize both.
- `ready_for_classify` is literally the boolean `true`.
