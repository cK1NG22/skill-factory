# BP-003: Name is ≤64 chars, lowercase + hyphens + numbers only

**Source:** Anthropic skill-creator compliance checklist
**Category:** Frontmatter & description (Universal)

**Why:** Hard runtime limit. Names with spaces, uppercase, or special chars cause invocation errors. Reserved words ("anthropic", "claude") are blocked.

**When applicable:** Every skill (Universal).

**Enforced by:** `skill-frontmatter`, `skill-compliance`

**Correct:** `acme-onboarding`, `411-deck`, `skill-spec-validator`

**Incorrect:** `Acme_Onboarding`, `claude-helper`, `My Skill`
