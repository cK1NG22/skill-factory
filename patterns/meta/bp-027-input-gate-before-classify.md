# BP-027: Input gate before classify (`skill-spec-validator` runs first)

**Source:** Carter's hands-off vision
**Category:** Hands-off operation (Meta — factory pipeline structure)

**Why:** Single chokepoint for human-required clarity. Validator either green-lights or returns surgical gap-fills with line numbers and required-field hints. Keeps downstream pipeline confident-and-quiet.

**When applicable:** Driver (`skill-factory`). Factory-internal; not applied to client skills.

**Enforced by:** `skill-spec-validator` (Phase 1 of driver)

**Correct:** Phase 1 invokes validator. STATUS: pass → continue. STATUS: gaps → exit cleanly with fix-list.

**Incorrect:** Driver classifies first, then asks user 5 follow-up questions about the spec.
