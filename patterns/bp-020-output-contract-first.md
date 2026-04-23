# BP-020: Write the output contract FIRST (rendering contract)

**Source:** `feedback-deck-qa-checklist.md`; 411-refine refinement (baseline 0.572 → iter-1 0.827 on a single 8-line rendering-contract edit)
**Category:** Output & rendering (Universal — calibrated by complexity)

**Why:** When skills produce structured output, defining the output schema *before* the process steps eliminates ~40% of phase KPI misses. The contract forces inline rendering of all required sections, preventing "executive-summary-only" outputs that skip detail. **Promoted to Universal (calibrated) in Stage 3.5 (v3):** every skill declares its output shape; depth of the contract scales with output complexity.

**When applicable:** Every skill (Universal). Contract depth calibrates:
- Simple single-shot output (e.g., a JSON blob): ~5 lines, trivial contract.
- Structured multi-section output (e.g., a deck, a report, a checklist): full `## Required output structure` block listing every section.

**Enforced by:** `skill-output-contract`

**Correct:** SKILL.md opens Section 5 with a `## Required output structure` block listing every section the output MUST contain, calibrated to output complexity.

**Incorrect:** Output format is implied by the process; the model produces a vague summary.
