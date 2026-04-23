# BP-013: Ask user first, then suggest (never present-then-rubber-stamp)

**Source:** `tooling-skill-writing-patterns.md`
**Category:** Workflow & human-in-the-loop (Conditional — trait: `has_hitl`)

**Why:** Presenting a finished analysis and asking "looks good?" produces low-quality engagement. Asking the user what they think first, then layering Claude's analysis, produces actual collaboration.

**When applicable:** Skills with user gates mid-flow (trait: `has_hitl`).

**Enforced by:** `skill-phase-designer`

**Correct:** Phase 1: "What do YOU think the root problem is?" → wait → "Here's how that compares to common framings…"

**Incorrect:** Phase 1: "Here's the problem analysis I generated. Approve?"
