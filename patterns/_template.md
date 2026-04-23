# BP-NNN: <short imperative title describing the rule>

**Source:** <where this rule came from — a memory file, a past incident, a Carter feedback session, an Anthropic doc>
**Category:** <category name> (<Universal | Conditional — trait: `<trait>` | Meta — factory-internal>)

**Why:** <one paragraph explaining the problem this rule prevents, with a concrete example of what goes wrong without it. LLMs follow reasoning better than directives — this is the "because" per BP-014.>

**When applicable:** <Universal → "Every skill." Conditional → "Skills with <trait fires when>." Meta → "Factory-internal; not applied to client skills.">

**Enforced by:** <which sub-skill(s) enforce this + any complementary compliance-check that catches violations>

**Correct:** <concrete example of the rule applied correctly>

**Incorrect:** <concrete example of the rule violated — ideally the WRONG thing a novice would do>

---

## How to use this template

1. Copy this file to `patterns/bp-NNN-<slug>.md` (or `patterns/meta/bp-NNN-<slug>.md` if Meta).
2. Fill every section. Every entry must answer: what is the rule, why does it exist, when does it apply, who enforces it, what's correct vs incorrect.
3. Add a row to `PATTERNS.md` (the index) in the correct category section.
4. If Conditional, add/update the trait mapping in `SKILLS.md`.
5. Submit PR with title `patterns: BP-NNN <short name>`.
