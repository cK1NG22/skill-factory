# BP-014: Add rationale with "because" — explain WHY

**Source:** `tooling-skill-writing-patterns.md`; reinforced in Anthropic skill-creator (lines 318-321)
**Category:** Workflow & human-in-the-loop (Universal)

**Why:** LLMs follow reasoning better than directives. Rationale also helps handle edge cases the skill description doesn't cover. ALL-CAPS MUSTs without rationale are a yellow flag.

**When applicable:** Every skill (Universal), especially anywhere the skill imposes a non-obvious constraint.

**Enforced by:** all sub-skills (review for "because" clauses)

**Correct:** `Generate 3–5 candidate solutions — because exhausting the solution space before committing prevents anchoring on the first good idea.`

**Incorrect:** `Generate 3–5 candidate solutions. ALWAYS.`
