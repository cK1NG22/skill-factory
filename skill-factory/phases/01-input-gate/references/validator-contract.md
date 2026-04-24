# Validator contract — what `/skill-spec-validator` expects and emits

Phase-scoped reference for Phase 1. Cited by `../director.md`.

## Input the validator expects

A single argument: an absolute path to a `client-spec.md` file. The
validator does NOT read any other context — it treats the spec as a
self-contained document per BP-033.

## The 10 required spec sections

The validator checks that the spec contains every one of these headings
and that each section has non-empty content:

1. `## Company`
2. `## Skill slug`
3. `## One-line description`
4. `## Inputs`
5. `## Outputs`
6. `## Happy-path walkthrough`
7. `## Failure modes`
8. `## Existing skills to reuse`
9. `## Reference-worthy domain knowledge`
10. `## Scheduling` (may be "N/A" but the section must exist)

Any missing section → `status: gaps` with a specific fix instruction.

## Optional sections the validator recognizes

- `## Edge cases`
- `## Anti-goals`
- `## Hooks needed`

These are surfaced in the `optional_present` array of `output.yaml` but
their absence is not a gap.

## What the validator rejects beyond missing sections

- **BP-034 violation:** a `## Existing skills to reuse` section naming a
  `/<skill>` that does not exist in the local ecosystem (the validator
  stat-checks `~/.claude/skills/<skill>/`).
- **Non-verbatim trigger phrases** in the `One-line description` that
  won't match `skill-frontmatter`'s BP-001 / BP-002 rules.
- **Combined skill-name length > 64 chars** (`<company>-<slug>`).

See `skill-spec-validator/references/spec-requirements.md` for the full
10-rule + 6-optional schema.

## Output shape the Phase 1 director reads

The validator writes three files to its phase directory:

- `output.yaml` — machine-readable verdict. The driver reads `status`
  and (on `gaps`) `missing` / `ambiguous` lists.
- `output.md` — human-readable gap report or pass confirmation.
- `notes.md` — validator observations (useful for debugging but not
  part of the driver's branching logic).

## Why Phase 1 is a hard wall

Per BP-027, auto-repair of a spec is out of scope for the factory. The
client supplies a validated spec or the factory halts. This invariant
exists because the downstream sub-skills' context packs are built from
the spec; if the spec is broken, the packs are broken, and the sub-skills
produce garbage without any clear upstream failure signal.

## Exit conditions

- `status: pass` → Phase 1 hands off to Phase 2 with the spec path and
  the validator's `output.yaml` path both recorded.
- `status: gaps` → Phase 1 prints the gap report to the user and stops.
  No further phases run.
