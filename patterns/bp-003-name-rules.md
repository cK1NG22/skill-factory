# BP-003: Name is ≤64 chars, lowercase + hyphens + numbers only

**Source:** Anthropic skill-creator compliance checklist
**Category:** Frontmatter & description (Universal)

**Why:** Hard runtime limit. Names with spaces, uppercase, or special chars cause invocation errors. Reserved words ("anthropic", "claude") are blocked.

**When applicable:** Every skill (Universal).

**Enforced by:** `skill-frontmatter`, `skill-compliance`

**Correct:** `acme-onboarding`, `411-deck`, `skill-spec-validator`

**Incorrect:** `Acme_Onboarding`, `claude-helper`, `My Skill`

## Meta-skill exception (Stage 10c)

**Surfaced by:** Stage 9c self-bootstrap (the factory regenerated itself
under the slug `skill-factory-skill-factory`, vs the committed slug
`skill-factory`).

**Rule:** Factory-internal sub-skills are exempt from the implicit
`<company>-<slug>` convention. The 8 meta-skill slugs as of Stage 10c are:

- `skill-compliance`
- `skill-spec-validator`
- `skill-frontmatter`
- `skill-phase-designer`
- `skill-references-scaffolder`
- `skill-cron-observability`
- `skill-signed-handoff`
- `skill-compliance-gate`
- `skill-factory` (the driver)

**Why:** "skill" is the de-facto company prefix for factory-internal
artifacts. Enforcing `skill-skill-X` is awkward, brittle, and provides no
behavioral benefit. Renaming the 8 sub-skills would be cosmetic-only and
break every existing reference in the patterns + driver tree.

**Marker:** Meta-skills declare themselves via a `meta-skill: true`
frontmatter line. The compliance gate's Check 14 (meta-BP citation scan,
the Stage 10a contract) skips skills that carry this marker — those
artifacts legitimately cite factory-internal meta-BPs (BP-028, BP-033,
patterns/meta/bp-*) because those govern factory-internal behavior. A
client skill citing the same patterns would still be flagged.

**Enforcement of the marker:**

- `compliance_check.py` accepts `meta-skill` as a valid frontmatter key
  (Stage 10c addition to `ALLOWED_KEYS`).
- `frontmatter_lint.py` accepts `meta-skill` in `_ALLOWED_TOP_KEYS`.
- `skill-compliance-gate/scripts/gate.py` auto-detects the marker via
  `is_meta_skill(skill_path)` and skips Check 14. The CLI `--meta-skill`
  flag forces the skip explicitly (used for testing client fixtures
  + bonus sweeps that audit the factory itself).

**What this exception does NOT change:**

- BP-003's name format (kebab-case, ≤64 chars, no consecutive hyphens,
  no reserved words) still applies to meta-skills.
- Compliance check #3 (`name_format`) runs unchanged on meta-skills.
- All other 13 checks run normally; only Check 14 is gated by the marker.
