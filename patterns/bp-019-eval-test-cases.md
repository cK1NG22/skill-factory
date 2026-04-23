# BP-019: Eval test cases are realistic, substantive, and cover near-miss negatives

**Source:** Anthropic skill-creator description optimization (lines 360–376)
**Category:** KPIs & evaluation (Universal — artifact discipline)

**Why:** Simple queries ("read this PDF") don't trigger skills regardless of description quality. Near-miss negatives (queries that share keywords with should-trigger but actually need something different) are the hardest test and the most discriminating. **Promoted to Universal in Stage 3.5 (v3):** writing `trigger-evals.md` artifacts is cheap and makes every skill description-optimization-ready. **Running** the optimization loop is gated by `--polish-triggers`.

**When applicable:** Every skill (Universal — artifact). Factory produces `trigger-evals.md` (8–10 should-fire + 8–10 near-miss should-not-fire queries) for every client skill.

**Enforced by:** `skill-description-triggers` (artifact writer); optimization loop gated by CLI flag.

**Correct:** Realistic prompts with file paths, casual tone, edge cases. 8–10 should-trigger + 8–10 should-NOT-trigger near-misses.

**Incorrect:** "Format this data" as the should-trigger query and "Write a fibonacci function" as the should-not-trigger.
