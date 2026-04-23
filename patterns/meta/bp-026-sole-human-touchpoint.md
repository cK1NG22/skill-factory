# BP-026: Sole human touchpoint = the input spec

**Source:** Carter's hands-off vision (skill-factory plan, Phase 4 round 2)
**Category:** Hands-off operation (Meta — factory design)

**Why:** The factory's quality ceiling is set by the input spec. Every mid-pipeline pause is a quality leak — the spec should have answered that question. Hands-off discipline forces every ambiguity back to the validator stage.

**When applicable:** The driver (`skill-factory`) and any pipeline-orchestrator built atop it. Factory-internal; not applied to client skills (many client skills are themselves HITL).

**Enforced by:** `skill-factory` driver design — no `AskUserQuestion` calls past Phase 1.

**Correct:** Spec passes validator → factory runs end-to-end → produces 13/13-compliant skill.

**Incorrect:** Mid-pipeline `AskUserQuestion("which approach should I take?")`.
