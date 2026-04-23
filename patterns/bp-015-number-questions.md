# BP-015: Number all questions, use `AskUserQuestion` for choices

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Workflow & human-in-the-loop (Conditional — trait: `has_hitl`)

**Why:** Numbered questions get answered in full; unnumbered prompts get partial responses. `AskUserQuestion` (vs plain text) is the right tool for choices because it provides structured options instead of free-text guessing.

**When applicable:** Skills with user gates mid-flow (trait: `has_hitl`).

**Enforced by:** `skill-phase-designer`

**Correct:** `Answer all four before proceeding: 1. … 2. … 3. … 4. …` Or `AskUserQuestion(...)` with explicit options.

**Incorrect:** "Tell me about X, Y, and Z" — usually returns just X.
