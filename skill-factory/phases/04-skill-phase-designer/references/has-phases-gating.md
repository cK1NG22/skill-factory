# has_phases predicate — firing conditions and edge cases

Phase-scoped reference for Phase 4. Cited by `../director.md`.

## The predicate

`has_phases.fires` is `true` when the client spec's `## Happy-path
walkthrough` section contains:

- Numbered markdown headings like `## 1. Foo`, `## 2. Bar`.
- An explicit `## Procedure` heading.
- An explicit `## Workflow` heading.
- A numbered list where each item is 3+ lines (not just one-liner tasks).

It is `false` when the walkthrough is:

- Short prose (a single paragraph).
- A bulleted list of one-liners.
- A single unnumbered code block.

## The 4 documented edge cases

From the parent factory's `trait-edge-cases.md` §has_phases:

1. **Alt-naming:** `## Workflow` is treated identically to
   `## Procedure`. The 411-research skill surfaced this case.
2. **Numbered sub-sections:** `## 1. Foo` fires the predicate even
   without a top-level `## Procedure`. Prevents authors from hiding
   phases behind numbered top-level headings.
3. **Code-block-only walkthroughs:** if the walkthrough is ONE fenced
   code block with N shell commands, `has_phases` does NOT fire — that
   is a one-shot transformation, not a phased procedure.
4. **≥3-step threshold downstream:** the classifier fires on any
   numbered structure, but `skill-phase-designer` itself hard-BLOCKERs
   on <3 numbered items in the walkthrough. The driver trusts the
   classifier's verdict; the sub-skill is the gate that catches
   "structured but too short to be a real phased procedure."

## Why Phase 4 and Phase 7 both read `has_phases`

Phase 4 (`skill-phase-designer`) fires on `has_phases` alone.
Phase 7 (`skill-signed-handoff`, Wave 3) fires on the intersection
`has_phases ∧ invokes_skills`. Both read the same `has_phases.fires`
boolean; they just combine it with other predicates differently.

The factory does NOT define a separate `has_signed_handoff` trait
because BP-024 rides exactly on the `has_phases` ∧ `invokes_skills`
intersection (phased skills that hand off to other skills). Inventing a
7th trait would be redundant. This is captured in ADR-0001's 5-trait
sufficiency argument.

## What this phase does NOT decide

- Does NOT decide whether HITL applies. `has_hitl` is a separate trait
  (fires on explicit user-interaction markers in the walkthrough).
  Phase 4 reads `has_hitl` only to pass the `--hitl` flag to
  phase-designer's lint — it does not re-derive the HITL verdict.
- Does NOT decide whether references are needed. `has_references` is
  separate; Phase 5 (Wave 3) handles that gate.
