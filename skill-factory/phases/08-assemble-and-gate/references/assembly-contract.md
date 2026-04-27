# `assemble_skill.py` contract

Phase-scoped reference for Phase 8a (the inline assembly step). Cited by
`../director.md` Step A.

## Per-phase output → assembled-file mapping

`assemble_skill.py` reads `<work>/classifier.json` to determine which
optional phases fired, then pulls phase outputs accordingly:

| Source under `<work>/phases/...` | Destination in `<work>/assembled/<slug>/` | When |
|---|---|---|
| `03-skill-frontmatter/output.yaml` | top of `SKILL.md` (frontmatter block) | always |
| `03-skill-frontmatter/input.md` `### One-line description` | body intro of `SKILL.md` | always (best-effort) |
| `03-skill-frontmatter/input.md` `### Happy-path walkthrough` | `## Happy-path walkthrough` section of `SKILL.md` | always (best-effort) |
| `04-skill-phase-designer/output.md` | `## Procedure` section of `SKILL.md` | when `has_phases.fires` |
| `05-skill-references-scaffolder/target/references/*.md` | `references/*.md` | when `has_references.fires` |
| `06-skill-cron-observability/instrumentation-snippet.md` (python fence) | `scripts/instrumentation_snippet.py` | when `is_scheduled.fires` |
| `07-skill-signed-handoff/output-signature-template.py` | `scripts/<slug>_signature.py` | when `has_phases.fires ∧ invokes_skills.fires` |

If `has_phases.fires` is true, the assembler also creates an empty
`phases/` directory in the assembled tree. This is structural scaffolding
for BP-009 (parallel folders); the actual phase directors are authored
post-factory by the user (Stage 11+ scope).

## ASSEMBLY-MANIFEST.json schema

`assemble_skill.py` writes a manifest into the assembled tree. Schema:

```json
{
  "slug": "<assembled-skill-slug>",
  "firing_traits": ["has_phases", "has_references", ...],
  "skill_md": "SKILL.md",
  "from_phases": {
    "03-skill-frontmatter": ["output.yaml"],
    "04-skill-phase-designer": ["output.md"]
  },
  "references": ["alpha.md", "beta.md"],
  "scripts": ["instrumentation_snippet.py", "<slug>_signature.py"]
}
```

`firing_traits` is sorted lexicographically for stable diffs. `references`
and `scripts` are present only when the corresponding phases contributed
files.

The Stage 10c self-bootstrap diff reads this manifest to verify byte-level
equivalence between the regenerated `skill-factory/` directory and the
committed-state directory.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success. Assembled dir exists at `<work>/assembled/<slug>/`. |
| 1 | Required phase output missing (e.g. `has_phases.fires` but no `04-skill-phase-designer/output.md`). |
| 2 | Malformed phase output (e.g. empty `output.yaml`, malformed `classifier.json`). |

The Phase 8 director maps both 1 and 2 to a `BLOCKER:` line per BP-028 —
the user re-runs the factory after fixing the upstream phase.

## Why assembly is inline and not a sub-skill

Per Stage 10 plan default D3, assembly is mechanical file movement — there
is no spec authorship, no compliance reasoning, and no cross-skill reuse
that would justify a sibling sub-skill (BP-034). It lives at
`skill-factory/scripts/assemble_skill.py` so it can co-evolve with the
phase-output formats it consumes (BP-031).

The compliance gate IS a sub-skill because it cross-uses
`compliance_check.py` from `skill-compliance` (the BP-034 trigger).
Assembly does not — it only reads files this driver wrote.
