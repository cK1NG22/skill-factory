# Phase 2 — Trait classification (director)

Phase 2 always fires. It runs the 5-predicate classifier over the
validated spec and writes `classifier.json` to the work directory. Every
conditional phase downstream (Phase 4, and Stages 9a/9b's 5, 6, 7) reads
this file to decide whether to enter.

## Procedure

1. **Run the classifier** over the validated spec:

   ```bash
   python3 ~/Projects/skill-factory/skill-factory/scripts/trait_predicates.py \
       spec <spec-path> > <work>/classifier.json
   ```

2. **Verify the JSON is well-formed.** If `trait_predicates.py` exits
   non-zero or the output is not parseable JSON, STOP — a classifier
   crash is a factory bug, not a retry condition. Surface the error and
   halt.
3. **Record the verdict** for Phase 99's final report. No further action
   in this phase — Phase 2 does not invoke any sub-skill.

See `references/classifier-cli.md` for the classifier's mode flags, the
5-trait schema, and the 4 documented edge cases.

## The 5-trait schema

| Trait fires → | Conditional BPs activated |
|---|---|
| `has_references` | BP-007 |
| `has_phases` | BP-009, BP-010 |
| `has_hitl` | BP-011, BP-012, BP-013, BP-015, BP-016 |
| `is_scheduled` | BP-022 |
| `invokes_skills` | BP-023 (always) + BP-024 (iff also `has_phases`) |

**12 Universal BPs always fire** — see `../../../PATTERNS.md` at repo
root for the full list.

## What this phase does NOT do

- Does NOT invoke any sub-skill. The classifier is a pure-stdlib Python
  function, not a sub-skill subagent.
- Does NOT re-validate the spec. Phase 1 is the sole validation gate;
  Phase 2 trusts the spec.
- Does NOT decide which sub-skills fire. It writes the traits JSON; each
  conditional phase director reads the JSON and decides per
  `../../references/trait-gating.md`.

## Cross-reference

- Trait-gating patterns shared across conditional phases:
  `../../references/trait-gating.md`.
- The full 5-trait schema + edge cases the classifier handles:
  `references/classifier-cli.md`.
