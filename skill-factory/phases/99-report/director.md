# Phase 99 — Report and stop (director)

Phase 99 always fires. It is the factory's terminus — once it runs, the
driver exits cleanly. There is no sub-skill invocation and no retry loop.
Phase number `99` is intentional: it reserves `05`–`07` for the Wave 3
conditional phases (references-scaffolder, cron-observability,
signed-handoff) added in Stages 9a and 9b without renumbering this
terminal phase.

## Procedure

Print, in order:

1. **Phase 1 verdict** — the validator's `status: pass` confirmation and
   the count of optional sections the spec included.
2. **Phase 2 trait JSON** — the 5-trait block from `classifier.json`.
3. **Applied BP list** — the union of the 12 Universal BPs plus every
   Conditional BP activated by a firing trait (see the trait-to-BP table
   in `../02-trait-classification/director.md`).
4. **Phase 3 outputs** — the final `output.yaml` frontmatter and the
   rationale section from `output.md`.
5. **Phase 4 outputs (if it ran)** — the `## Procedure` section from
   `output.md`.
6. **Phase 5 outputs (if it ran — Wave 3)** — the scaffolded references
   tree description.
7. **Phase 6 outputs (if it ran — Wave 3)** — the cron-observability
   instrumentation snippet.
8. **Phase 7 outputs (if it ran — Wave 3)** — the stamped
   `<slug>_signature.py` path + lint verdict.
9. **All `notes.md` observations** from every phase that wrote one.
10. **The work directory path** — `<work>/`, so the user can navigate
    the filesystem to review everything.

## Status sentence

Until Wave 3 ships the 3 remaining sub-skills, the report ends with a
status sentence naming which phases are not yet orchestrated. After
Wave 3, the sentence updates to either "all 5 conditional phases live"
or "Phase 8+ deferred to Stage 10+" depending on what has shipped.

## What this phase does NOT do

- Does NOT create a per-client repo. That's a post-Stage-10 scope item
  (not yet planned as of Stage 9).
- Does NOT commit anything to git.
- Does NOT hand-install any artifact into a target skill directory —
  the user reviews the work directory and grafts artifacts manually.
- Does NOT loop or retry. Phase 99 runs exactly once per factory
  invocation. If any upstream phase hit a BLOCKER and halted, Phase 99
  does not run at all — the driver exits at the BLOCKER point.

## Cross-reference

- Universal BP list: `../../../PATTERNS.md`.
- Trait → Conditional BP mapping: `../02-trait-classification/director.md`.
