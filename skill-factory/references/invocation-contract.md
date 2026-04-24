# The input.md invocation contract (BP-033)

Cross-phase reference shared by every phase director that invokes a sub-skill.
Codifies the BP-033 contract between the driver (which materializes context
packs) and sub-skills (which read ONLY their own `input.md`).

## The contract

For each sub-skill target, the driver writes exactly one file:

```
<work>/phases/<N>-<sub-skill-name>/input.md
```

The sub-skill reads ONLY this file. It does not read the spec, the
classifier JSON, other phases' input.md, or any file the `input.md` does
not explicitly name.

## Pack shape

Every `input.md` has this section order:

1. **`# Task`** — one-line imperative statement of what the sub-skill produces.
2. **`## Spec excerpt`** — the subset of the validated spec fields this
   sub-skill needs (different sub-skills need different subsets — the pack
   builder's `_SUB_SKILL_SECTIONS` registry decides).
3. **`## Classified traits`** — the 5 traits with their `fires` booleans,
   rendered as a flat sub-section. The sub-skill consults this to gate its
   own conditional rules (e.g. `skill-phase-designer` checks `has_hitl` to
   know whether to enforce BP-011/012/013/015/016).
4. **`## BPs to enforce`** — absolute paths to the pattern files in
   `patterns/` that this sub-skill must cite in its output. The sub-skill
   reads each listed path; it does NOT read the full `patterns/` catalog.
5. **`## Output locations`** — absolute paths where the sub-skill writes
   its output files (at minimum `output.md` and `notes.md`; some sub-skills
   also write `output.yaml` or other named artifacts).

## Registration surface

New sub-skills are registered in `scripts/build_context_pack.py` via six
dicts (see the Tier-1 / Tier-2 author cheat-sheet in that module's
docstring). The `input.md` format is the same across all sub-skills; the
registries only vary which sections, which BPs, and which output paths
are materialized.

## Why the contract exists

Without this contract, a sub-skill could reach into the driver's state,
the spec, or other phases' artifacts — and then a downstream change to any
of those would silently break the sub-skill. With the contract:

- **Sub-skills are pure functions of their `input.md`.** Deterministic.
- **Pack shape regressions fail fast.** The pack builder's tests lock the
  exact section order and content shape per sub-skill.
- **Adding a sub-skill is local work.** Register it in the 6 dicts; no other
  file changes.

## What the driver does NOT do

- Does NOT hand the sub-skill the raw spec. The pack builder excerpts only
  the sections the sub-skill needs.
- Does NOT hand the sub-skill the classifier JSON. The pack builder renders
  a flat `## Classified traits` block from it.
- Does NOT create any output files in the sub-skill's phase directory. The
  sub-skill creates its own outputs at the paths the `## Output locations`
  section names.

## Cross-reference

- Agent-spawn mechanics: `spawn-subagent.md`.
- Trait-fires gating (which phases fire at all): `trait-gating.md`.
- BP-033 canonical text: `../../patterns/bp-033-driver-materialized-context-packs.md`.
