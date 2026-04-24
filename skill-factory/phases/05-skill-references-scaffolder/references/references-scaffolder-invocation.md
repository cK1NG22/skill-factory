# skill-references-scaffolder invocation contract (phase-scoped)

Phase-scoped reference for Phase 5. Cited by `../director.md`.

## Pack shape

`build_context_pack.py <spec> <classifier.json> skill-references-scaffolder
<out-dir> --target-skill-dir <dir>` materializes `input.md` with these
sections:

1. **`# Task`** — "Verify the pre-scaffolded references/ tree and emit
   the scaffolder's plan."
2. **`## Spec excerpt`** — base sections: `Company`, `Skill slug`,
   `One-line description`, `Reference exemplars`, `Happy-path
   walkthrough`. The `Reference exemplars` body lists each reference
   filename and a one-line purpose.
3. **`## Classified traits`** — the 5 traits.
4. **`## BPs to enforce`** — base is BP-007 (loaded on demand) +
   BP-008 (one level deep). When `has_phases.fires: true`, the union
   adds BP-009 (parallel folders).
5. **`## Target skill directory`** — absolute path to the scaffolded
   tree the sub-skill walks (driver-injected via `--target-skill-dir`).
6. **`## Output locations`** — `output.md`, `notes.md`.

## BP-set breakdown

Always applied (base, fired by `has_references`):
- **BP-007** — Detail in `references/`, loaded on demand.
- **BP-008** — `references/` is one level deep.

Added when `has_phases.fires: true` (via `_SUB_SKILL_CONDITIONAL_BPS`):
- **BP-009** — Parallel folders for complex skills (`phases/` and
  `references/` are siblings; no `phases/*/references/` nesting).

## Lint flags the driver passes

| Trait fires | `references_lint.py` flag |
|---|---|
| `has_references` | `--has-references` (always — entry gate) |
| `has_phases` | `--has-phases` |

## The pre-scaffold contract

The sub-skill is a **verifier**, not a creator. It walks an existing
target skill directory and lints its `references/` tree. In driver
mode, the target skill does not yet exist, so the driver pre-scaffolds
it before invoking the sub-skill.

The driver's pre-scaffold pass (Step 1 in `../director.md`) runs
`build_context_pack.py --prescaffold-references <spec> <target-dir>`,
which:

1. Parses the spec's `Reference exemplars` section into
   `[(filename, purpose), ...]`.
2. Creates `<target-dir>/references/<filename>` for each entry —
   empty placeholder, single `# <stem>` header.
3. Creates `<target-dir>/SKILL.md` with stub frontmatter + a
   `## References` section containing one canonical
   `Read references/<name>.md for <purpose>.` line per entry.

The sub-skill then walks the populated tree, verifies citations,
runs its own lint, and emits `output.md` (the scaffolder's plan).

## BLOCKER causes

- **Empty `Reference exemplars` section** with `has_references` fired —
  classifier and spec disagree. Pre-scaffold returns empty list; sub-
  skill BLOCKERs.
- **Two consecutive lint failures** on the scaffolded tree — sub-skill
  internally retries once, then BLOCKERs per BP-028.
- **Target skill directory missing** — pre-scaffold step failed
  silently, OR the driver passed an unwriteable path. Sub-skill
  BLOCKERs at its own Step 4.

## output.md shape the driver reads

A structured plan with these headings:
- `## Citations to splice` — `<filename> → "<canonical citation line>"`
- `## BP-008 violations` (if any) — sub-directories under `references/`
- `## BP-009 violations` (if any, when `has_phases` fires) — nested
  `phases/*/references/` paths
- `## Move to references/` (if any) — inline tables / dense prose in
  SKILL.md that should be extracted

The driver hands this to Phase 99 as-is; the user manually applies the
plan against the final skill repo.
