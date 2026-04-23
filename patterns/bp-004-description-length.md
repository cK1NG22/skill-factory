# BP-004: Description ≤1024 chars

**Source:** Anthropic skill-creator compliance checklist
**Category:** Frontmatter & description (Universal)

**Why:** Descriptions get truncated past 1024 chars; trigger phrases at the end are silently dropped, breaking discoverability.

**When applicable:** Every skill (Universal).

**Enforced by:** `skill-frontmatter`, `skill-compliance`

**Correct:** ~600–900 chars including 5–10 trigger phrases and a "Do NOT use for…" negative-case clause.

**Incorrect:** A 1500-char essay describing the skill's history and rationale.
