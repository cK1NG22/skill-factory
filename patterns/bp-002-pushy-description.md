# BP-002: Description must be slightly "pushy"

**Source:** Anthropic skill-creator (line 67)
**Category:** Frontmatter & description (Universal)

**Why:** Claude's default behavior is to NOT consult skills for tasks it thinks it can handle directly. "Pushy" means listing concrete trigger phrases, naming the skill explicitly in those triggers, and making the use-cases unambiguous. Soft descriptions get skipped.

**When applicable:** Every skill (Universal).

**Enforced by:** `skill-frontmatter`, `skill-description-triggers`

**Correct:** Lists 5–10 verbatim trigger phrases in quotes; names file types, tools, or domains.

**Incorrect:** Generic verbs without context ("creates a document", "generates a report").
