# BP-005: `allowed-tools` declared in frontmatter

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Frontmatter & description (Universal)

**Why:** Without `allowed-tools`, every tool use mid-skill triggers a permission prompt — disruptive and breaks long workflows. Pre-declaring authorizes the tools at skill load.

**When applicable:** Every skill (Universal), especially HITL/pipeline that span many tool calls.

**Enforced by:** `skill-frontmatter`, `skill-compliance`

**Correct:** `allowed-tools: [AskUserQuestion, Agent, Read, Write, Bash, WebFetch]`

**Incorrect:** Frontmatter omits `allowed-tools`; user gets prompts mid-flow.
