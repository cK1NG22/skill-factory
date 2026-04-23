# Expected validator output for `fixtures/bp-034-spec.md`

This spec tests the BP-034 check. All 10 required sections are present and well-formed, BUT the "Existing skills to reuse" section names `/acme-generate-email` which does not exist in the ecosystem. Per BP-034, sub-skills are only for cross-skill reuse; if `/acme-generate-email` would only be used by this one skill, it should stay as a reference file (e.g., `references/email-generation.md`) inside `/acme-onboarding-checklist` rather than being extracted into its own skill.

## Expected `output.yaml`

```yaml
status: gaps
spec_path: /absolute/path/to/fixtures/bp-034-spec.md
missing_required: []
ambiguous_required:
  - section: "Existing skills to reuse"
    line: <line-number of the /acme-generate-email line in the spec>
    issue: "Spec names '/acme-generate-email' as a reused skill, but /acme-generate-email does not exist at ~/.claude/skills/. Per BP-034, this violates the cross-skill reuse discipline — it appears the spec is proposing to extract a sub-process into its own sub-skill even though no other skill uses it."
    fix: "The skill '/acme-generate-email' named here does not exist at ~/.claude/skills/acme-generate-email/. Per BP-034, sub-skills are only for cross-skill reuse — single-skill sub-processes stay as reference files. Either (a) create '/acme-generate-email' as a first-class ecosystem skill with its own reuse justification BEFORE building this one, or (b) remove it from this section and add the sub-process as a `references/<topic>.md` file inside this skill instead."
optional_present: []
ready_for_classify: false
```

## Expected `output.md`

Human-readable version containing:

- Header: `STATUS: gaps`
- Summary: 0 missing required sections, 1 ambiguous required section.
- The ambiguous_required entry formatted as:
  > **Existing skills to reuse** (line N): Spec names '/acme-generate-email' as a reused skill, but /acme-generate-email does not exist at ~/.claude/skills/. Per BP-034, this violates the cross-skill reuse discipline — it appears the spec is proposing to extract a sub-process into its own sub-skill even though no other skill uses it.
  >
  > **Fix:** The skill '/acme-generate-email' named here does not exist at ~/.claude/skills/acme-generate-email/. Per BP-034, sub-skills are only for cross-skill reuse — single-skill sub-processes stay as reference files. Either (a) create '/acme-generate-email' as a first-class ecosystem skill with its own reuse justification BEFORE building this one, or (b) remove it from this section and add the sub-process as a `references/<topic>.md` file inside this skill instead.

## Why this fixture matters

It exercises the one case where all 10 required sections structurally pass but a content-level BP violation gets flagged. This proves the validator is not just a syntactic checker — it enforces semantic discipline from the patterns catalog when a BP has a content-rule of its own.

## How a spec author would fix this

Two options per BP-034:

1. **The sub-skill is genuinely cross-cutting.** Build `/acme-generate-email` first as its own spec-driven skill (run `/skill-factory acme generate-email-spec.md`), confirm it lands in `~/.claude/skills/acme-generate-email/`, then re-run this spec through the validator.

2. **The sub-skill is single-use.** Change this spec's happy-path walkthrough to: "…compose the HR notification email per the template in `references/email-generation.md` …" and remove the `/acme-generate-email` line from "Existing skills to reuse" (or replace it with `None` if no other skills are used).
