# BP-001: Description must include explicit trigger phrases

**Source:** Anthropic skill-creator + `tooling-skill-writing-patterns.md`
**Category:** Frontmatter & description (Universal)

**Why:** Claude undertriggers skills when descriptions lack literal trigger phrases. Description is the only signal the dispatcher uses to decide whether the skill applies. Past incident: 411-refine wouldn't fire on "use after research" because Claude expected "use when".

**When applicable:** Every skill (Universal).

**Enforced by:** `skill-frontmatter`, `skill-description-triggers`

**Correct:** `"Convert markdown to docx. Use when 'convert markdown to docx', 'md to word doc', 'turn this md into word'."`

**Incorrect:** `"Generates documents."`
