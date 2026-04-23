# BP-010: Apply once, carry forward, reference later

**Source:** `tooling-skill-writing-patterns.md`; emerged from 411-case build
**Category:** File structure & references (Conditional — trait: `has_phases`)

**Why:** Each reference file should be read at the FIRST phase where its knowledge is needed. The phase's output carries the insight forward. Later phases reference *the output*, not the original file. Eliminates redundant reads, keeps each phase focused.

**When applicable:** Skills with 3+ phases (trait: `has_phases`). Also applies to the skill-factory driver↔sub-skill pipeline: the driver is the single reader of shared references; sub-skills receive pointers to specific BP file paths (see BP-033).

**Enforced by:** `skill-phase-designer` (intra-skill), `skill-factory` driver (inter-Agent)

**Correct:** Phase 1 reads `references/strategy-overview.md`, writes its synthesis to `phase-1-output.md`. Phase 4 reads `phase-1-output.md`, not strategy-overview again.

**Incorrect:** Every phase opens with "Re-read references/strategy-overview.md."
