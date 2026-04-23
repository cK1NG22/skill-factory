# BP-024: Signed handoffs between pipeline skills (sha256 over argument-bearing fields)

**Source:** `411-deck-signed-handoff.md`; emerged from `/411-case → /411-deck` drift problem
**Category:** Composition & pipelines (Conditional — traits: `has_phases` ∧ `invokes_skills`)

**Why:** When skill A hands off content to skill B, B should be able to TRUST A's content without re-validating. Sha256 over argument-bearing fields (argument_flow, leadlines, callout_items, recommendation) lets B verify the contract was honored. Eliminates duplicate validation logic and drift.

**When applicable:** Skills where `has_phases` AND `invokes_skills` both fire — i.e., multi-phase skills that chain to other skills with a trust contract. This is the "pipeline orchestrator" case; it doesn't need its own trait because it's the intersection of two existing ones.

**Enforced by:** `skill-signed-handoff`

**Correct:** Upstream Phase 6 signs handoff via `scripts/deck_signature.py --sign`. Downstream Phase 1 verifies via `--verify`. Exit codes 0/1/2/3 surface specific failures.

**Incorrect:** Downstream re-validates argument structure from scratch; drift goes undetected.
