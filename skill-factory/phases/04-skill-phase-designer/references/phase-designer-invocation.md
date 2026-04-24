# skill-phase-designer invocation contract (phase-scoped)

Phase-scoped reference for Phase 4. Cited by `../director.md`.

## Pack shape

`build_context_pack.py <spec> <classifier.json> skill-phase-designer <out-dir>`
materializes `input.md` with these sections:

1. **`# Task`** — "Produce a `## Procedure` section for the skill
   described below, following the 6 phase-design rules."
2. **`## Spec excerpt`** — base sections: `Company`, `Skill slug`,
   `One-line description`, `Inputs`, `Outputs`, `Happy-path walkthrough`,
   `Failure modes`, `Existing skills to reuse`. When `has_hitl.fires:
   true`, the pack also includes `Success signals` and `Edge cases`.
3. **`## Classified traits`** — the 5 traits.
4. **`## BPs to enforce`** — base is BP-010 (sequential numbered steps)
   only. When `has_hitl.fires: true`, the union adds BP-011 (announce
   phase transitions), BP-012 (hard gates at reversibility boundaries),
   BP-013 (ask-user-first pattern), BP-015 (numbered inline questions),
   BP-016 (≤4 inline questions per step).
5. **`## Output locations`** — `output.md`, `notes.md`.

## BP-set breakdown

Always applied (base):
- **BP-010** — Sequential numbered steps, imperative-verb openings, no
  weak voice.

Added when `has_hitl.fires: true` (via `_SUB_SKILL_CONDITIONAL_BPS`):
- **BP-011** — Announce every phase transition in a human-visible line.
- **BP-012** — Hard gates ("Do NOT proceed until...") at reversibility
  boundaries.
- **BP-013** — Ask-user-first pattern before proposing alternatives.
- **BP-015** — Numbered inline questions (not AskUserQuestion for
  free-text), OR AskUserQuestion for explicit-choice cases.
- **BP-016** — ≤4 inline questions per step (more than 4 means the step
  should be split).

## Lint flags the driver passes

| Trait fires | `phase_lint.py` flag |
|---|---|
| `has_hitl` | `--hitl` |
| `invokes_skills` | `--invokes-skills` |

Omit either flag when the corresponding trait is `false`. Passing a flag
that the sub-skill's output doesn't use is harmless (the lint is more
strict, but the sub-skill's output wouldn't use HITL patterns anyway);
omitting a required flag is a silent regression (HITL content goes
unchecked).

## BLOCKER causes

- **Fewer than 3 numbered steps** in the walkthrough. The classifier
  fires `has_phases` on any numbered structure; the sub-skill enforces
  the minimum at BLOCKER time.
- **Two consecutive lint fails** on the internally-retried draft (per
  BP-028 discipline in the sub-skill's own SKILL.md).
- **HITL requirement missed** when `has_hitl.fires: true` but the
  Procedure has zero `Do NOT proceed` hard gates — the sub-skill
  internally retries once, then BLOCKERs if still failing.

## output.md shape the driver reads

A single `## Procedure` section with numbered `### Step N — <label>`
headings, each containing imperative-verb-opening body text. No
frontmatter, no other sections, no code blocks outside the step bodies.
The driver hands this to Phase 99 as-is; the user manually grafts it
into the target SKILL.md.
