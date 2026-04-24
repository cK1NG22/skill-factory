---
name: skill-references-scaffolder
description: Scaffold a factory-authored skill's references/ folder and verify SKILL.md cites each reference in canonical form. Use when "scaffold references", "wire up references", "check reference citations", "validate folder structure", "parallel folders check", "skill-references-scaffolder <workspace>", or when the skill-factory driver invokes this in Phase 4 because has_references or has_phases fires. Do NOT use for writing the SKILL.md frontmatter (use skill-frontmatter) or for drafting the Procedure section (use skill-phase-designer).
argument-hint: "<skill-dir-or-input-md-path>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-references-scaffolder

**Read ONLY your driver-supplied `input.md`** (per BP-033). The driver materializes it under `phases/05-skill-references-scaffolder/input.md` (Stage 9a wiring; the path is also embedded in your invocation prompt). The pack has distilled the spec's references list, the relevant trait verdicts (`has_references`, `has_phases`), and the specific BP file paths. Do NOT open the `patterns/` directory directly. Do NOT open the full spec file directly.

The one thing this skill produces: a populated `references/` folder (and a verified parallel-folder layout when `has_phases` fires) that passes `scripts/references_lint.py` against `references/references-rules.md`.

## What this skill does NOT do

- Does NOT author the SKILL.md frontmatter (that is `skill-frontmatter`'s job).
- Does NOT draft the Procedure section (that is `skill-phase-designer`'s job).
- Does NOT invent reference content beyond what the spec excerpt supplies.
- Does NOT move files outside the target skill's root directory.
- Does NOT invoke other sub-skills.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 5 when `has_references` fires (Stage 9a wiring; BP-009 parallel-folders rule unioned in via `_SUB_SKILL_CONDITIONAL_BPS` when `has_phases` also fires).

**Reads:**
- `phases/05-skill-references-scaffolder/input.md` — the driver-materialized context pack.

**Writes (to `phases/05-skill-references-scaffolder/`):**
- `output.md` — a structured plan naming the files to create under `references/`, the canonical citation lines to splice into SKILL.md, and the parallel-folder verdict.
- `notes.md` — `BLOCKER:` lines if any, otherwise short observations.

### Standalone (manual)

```
/skill-references-scaffolder <path-to-skill-dir-or-input.md>
```

## Procedure

Follow these steps in order.

### Step 1 — Load the input pack

Read `input.md`. The pack contains:
- **Task** — a one-line statement.
- **Spec excerpt** — the references list (topic + one-line purpose per entry), plus the Happy-path walkthrough so citation targets make sense.
- **Classified traits** — the 5 trait verdicts from Phase 2. Only `has_references` and `has_phases` matter for this sub-skill.
- **BPs to enforce** — absolute paths to the BP files. Always BP-008. BP-007 iff `has_references` fires. BP-009 iff `has_phases` fires.
- **Target skill directory** — absolute path to the skill root where `references/`, `phases/`, and `SKILL.md` live (or will live).
- **Output locations** — where to write `output.md` and `notes.md`.

If both `has_references` and `has_phases` are `false` in the pack, write `BLOCKER: skill-references-scaffolder invoked but neither has_references nor has_phases is true — driver bug` to `notes.md` and STOP. This sub-skill must never run when the trigger trait did not fire.

### Step 2 — Load the rules contract

Read `references/references-rules.md`. This is the authoritative source for Rules A, B, C.

### Step 3 — Read the listed BP files

For each `patterns/bp-NNN-*.md` path listed under "BPs to enforce", read the file. Do NOT read BP files not listed.

### Step 4 — Inspect the target skill root

Walk the target skill directory. Record:
- Does `SKILL.md` exist?
- Does `references/` exist? If so, list immediate-child `.md` files and flag any sub-directories.
- Does `phases/` exist? If so, look for any nested `phases/*/references/` paths.
- Does `assets/` exist?

If the target directory itself is missing, write `BLOCKER: target skill dir not found at <path>` to `notes.md` and STOP.

### Step 5 — Derive the reference file list from the spec

For each entry in the spec excerpt's references list, extract:
- `name` — kebab-case `.md` filename (e.g., `scoping-questions.md`).
- `purpose` — the one-line purpose the driver supplied.

If the spec references list is empty but `has_references` is true, write `BLOCKER: has_references fired but spec excerpt has no references list — upstream classifier and spec disagree` to `notes.md` and STOP.

### Step 6 — Plan the citation lines

For each reference file, construct exactly one canonical citation line in the form:

```
Read `references/<name>.md` for <purpose>.
```

Record the intended line in `output.md`. The line must use one of the canonical verbs (`Read`, `See`, `Consult`, `Load`, `Use`, `Refer to`, `per`) followed by the backtick-wrapped reference path.

### Step 7 — Verify Rule A (BP-008, universal if references/ exists)

If the target skill's `references/` folder has any sub-directory, list them in `output.md` under a `## BP-008 violations` heading and mark them for a human to flatten. Do NOT auto-move files — that is a destructive action the human must confirm. Record the BLOCKER condition in `notes.md`:

```
BLOCKER: references/ contains sub-directories; human must flatten per BP-008.
```

### Step 8 — Verify Rule B (BP-007, only if has_references)

If `has_references` fires:
- Cross-check the reference-file list from Step 5 against the existing files under `references/`. Name any extra files (present on disk but absent from the spec) in `output.md` as `orphan files` — flag for human review, do NOT delete.
- For each file from Step 5 not yet present in SKILL.md as a canonical citation, add the citation line from Step 6 to `output.md` under a `## Citations to splice` heading. Format: `filename → "<citation line>"`.
- Scan the current SKILL.md (if one exists) for inline tables (>=10 pipe-delimited rows) or dense prose spans (>=20 consecutive non-blank, non-heading lines). For each hit, record in `output.md` under `## Move to references/` with the line range and the suggested target filename.

If `has_references` is false, skip this step.

### Step 9 — Verify Rule C (BP-009, only if has_phases)

If `has_phases` fires:
- Confirm `phases/` and `references/` are siblings at the skill root.
- Walk for `phases/*/references/` and `references/*/phases/` nesting. Any hit goes under a `## BP-009 violations` heading in `output.md` with the relative path.
- If `assets/` is absent, record it as an informational observation in `notes.md` (warn, not blocker).

If `has_phases` is false, skip this step.

### Step 10 — Self-lint

Run the lint, passing the relevant trait flags extracted from Step 1's pack:

```bash
python3 scripts/references_lint.py <target-skill-dir> [--has-references] [--has-phases]
```

Pass `--has-references` iff the pack's `Classified traits` block has `has_references: true`. Pass `--has-phases` iff it has `has_phases: true`. The lint returns JSON with `passed`, `fails`, `warns`, `info`.

**If `passed: true`:** write `notes.md` with any warnings as informational observations. STOP. Task complete.

**If `passed: false` (first attempt):** apply the fix suggested by each `fails` entry. Re-run steps 5–9 as needed. Re-run the lint.

**If `passed: false` (second attempt):** write `BLOCKER: references_lint failed twice; see fails[] for details` to `notes.md`. Do NOT overwrite `output.md` with a broken plan. STOP. Human inspects per BP-028.

## Self-test

The skill ships with three fixtures under `fixtures/`:

**Passing (references only):**
```
/skill-references-scaffolder fixtures/passing-input.md
```
Expected: lint returns `passed: true` with `--has-references`. All reference files are cited canonically in the target SKILL.md; no nested sub-directories; no inline content blocks.

**Passing (parallel folders):**
```
/skill-references-scaffolder fixtures/passing-with-phases-input.md
```
Expected: lint returns `passed: true` with `--has-references --has-phases`. `phases/` and `references/` are siblings; no nesting; `assets/` present or warned.

**Gaps:**
```
/skill-references-scaffolder fixtures/gaps-input.md
```
Expected: lint returns `passed: false`. `notes.md` contains a `BLOCKER:` line. Violations include a nested `references/<sub>/` directory, an uncited reference file, and an inline 40-line table.

## Patterns enforced

- **BP-007** — detail in `references/`, loaded on demand (when `has_references`).
- **BP-008** — `references/` is one level deep (universal when the folder exists).
- **BP-009** — parallel folders for complex skills (when `has_phases`).
- **BP-028** — `BLOCKER:` convention when self-lint fails twice or input preconditions violated.
- **BP-033** — read only `input.md`, never open `patterns/` directly.

## What to do if you're stuck

- **`input.md` missing** → write `BLOCKER: input.md not found at <path>` to `notes.md`. Do not guess.
- **Target skill directory missing** → `BLOCKER: target skill dir not found at <path>`. Do not create it; that is the driver's job.
- **Neither `has_references` nor `has_phases` fires** → `BLOCKER: skill-references-scaffolder invoked but neither has_references nor has_phases is true — driver bug`. This sub-skill must not run when neither trait fired.
- **Spec references list empty with `has_references: true`** → `BLOCKER: has_references fired but spec excerpt has no references list`. Upstream classifier and spec disagree.
- **`references/` has sub-directories** → record as a BP-008 violation in `output.md` and surface in `notes.md`. Do NOT auto-flatten; a human must confirm destructive moves.
- **Two lint failures in a row** → `BLOCKER:`. Let a human inspect.

## Why this skill is strict

The `references/` folder is the lazy-load index for a skill. A reference file that SKILL.md never cites is unreachable; a nested folder defeats the flat-registry promise of BP-008; parallel-folder violations couple process and knowledge in a way that makes on-demand loading opaque. The deterministic lint catches structural issues that an eyeball review misses (an orphan file; a 35-line table inlined in SKILL.md; a `phases/phase-1/references/` that looks innocuous). Strict self-lint with forced BLOCKER on two failures is cheaper than a skill that silently carries dead or tangled knowledge paths into production.
