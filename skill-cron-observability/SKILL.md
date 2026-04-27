---
meta-skill: true
name: skill-cron-observability
description: Instrument a scheduled/cron skill with the BP-022 last-run/success/artifact contract and lint an existing cron skill's scripts to verify compliance. Use when "instrument this cron skill", "add cron observability", "generate cron last-run snippet", "lint cron observability", "verify cron skill writes latest.json", "skill-cron-observability <workspace>", or when the skill-factory driver invokes this in Phase 4 because is_scheduled fires. Do NOT use for non-scheduled skills, for writing the SKILL.md frontmatter (use skill-frontmatter), or for designing the Procedure steps (use skill-phase-designer).
argument-hint: "<phases-dir-or-input-md-path>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-cron-observability

**Read ONLY your driver-supplied `input.md`** (per BP-033). The driver materializes it under `phases/06-skill-cron-observability/input.md` (Stage 9a wiring; the path is also embedded in your invocation prompt). The pack has distilled the spec's Scheduling section, the relevant traits (`is_scheduled`), and the BP file paths. Do NOT open the `patterns/` directory directly. Do NOT open the full spec file directly.

The one thing this skill produces: an `instrumentation-snippet.md` — a copy-pasteable code block that wires the BP-022 observability contract into the target cron skill, plus a lint verdict on that snippet (or on an already-written `scripts/` directory).

## What this skill does NOT do

- Does NOT author the SKILL.md frontmatter (that is `skill-frontmatter`'s job).
- Does NOT lay out the `## Procedure` steps (that is `skill-phase-designer`'s job).
- Does NOT decide the references scaffold (that is `skill-references-scaffolder`'s job).
- Does NOT run on non-scheduled skills — if `is_scheduled` is false, surface a `BLOCKER:` and STOP.

## The BP-022 contract in one paragraph

Every cron/scheduled skill must answer three questions on demand: when did it last run, did it succeed, what did it produce. Canonical on-disk layout:

- `~/Claude/<skill>/runs/<timestamp>/result.json` — contains keys `last_run` (ISO-8601), `success` (bool), `artifact_path` (str).
- `~/Claude/<skill>/runs/<timestamp>/artifact.<ext>` — the actual output the skill produced on this run.
- `~/Claude/<skill>/latest.json` — a symlink (or a copy) pointing at the most recent run's `result.json`.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 6 when the `is_scheduled` trait fires.

**Reads:**
- `phases/06-skill-cron-observability/input.md` — the driver-materialized context pack.

**Writes (to `phases/06-skill-cron-observability/`):**
- `instrumentation-snippet.md` — a fenced Python block ready to paste into the target skill's cron orchestration.
- `output.md` — a short rationale wrapper around the snippet.
- `notes.md` — `BLOCKER:` lines if any, otherwise short observations.

### Standalone (manual)

```
/skill-cron-observability <path-to-input.md-or-its-parent-dir>
```

Or lint-only mode against an existing skill's scripts directory:

```
python3 scripts/observability_lint.py <path-to-scripts-dir-or-snippet.md>
```

## Procedure

Follow these steps in order.

### Step 1 — Load the input pack

Read `input.md`. The pack contains:
- **Task** — a one-line statement.
- **Spec excerpt** — the Scheduling section (required), the skill slug, the expected artifact extension (e.g. `.docx`, `.csv`, `.md`), and the Outputs section.
- **Classified traits** — the 5 trait verdicts from Phase 2. Only `is_scheduled` matters for this sub-skill.
- **BPs to enforce** — absolute paths to the BP files. Always BP-022. Optionally BP-021 (output home) and BP-028 (BLOCKER convention).
- **Output locations** — where to write `instrumentation-snippet.md`, `output.md`, and `notes.md`.

If `is_scheduled` is not `true` in the pack, write `BLOCKER: skill-cron-observability invoked but is_scheduled is false — driver bug` to `notes.md` and STOP. This sub-skill must never run on non-scheduled skills.

### Step 2 — Load the rules contract

Read `references/cron-observability-rules.md`. Four rules (A, B, C, D) govern the instrumentation. The lint script is authoritative — when the rules doc and the lint diverge, update the doc.

### Step 3 — Read the listed BP files

For each `patterns/bp-NNN-*.md` path listed under "BPs to enforce", read the file. Do NOT read BP files not listed.

### Step 4 — Parse the Scheduling section

Extract from the spec excerpt the cron frequency (e.g. `0 */6 * * *`, `@daily`, `every 5 minutes`) and the artifact extension (e.g. `.docx`, `.csv`, `.md`, `.json`).

If either field is missing, write `BLOCKER: Scheduling section missing cron frequency or artifact extension` to `notes.md` and STOP. Do NOT guess; surface the gap to the validator upstream.

### Step 5 — Determine the skill slug and output home

Read the skill slug from the input pack. Compute the output home as `~/Claude/<slug>/` per BP-021. The runs directory is `~/Claude/<slug>/runs/<timestamp>/`. The latest pointer is `~/Claude/<slug>/latest.json`.

### Step 6 — Generate the instrumentation snippet

Assemble a Python snippet that:
- Imports `json`, `os`, `datetime`, `pathlib`.
- Computes `timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")`.
- Builds `run_dir = Path("~/Claude/<slug>/runs/") / timestamp` and calls `run_dir.mkdir(parents=True, exist_ok=True)`.
- Writes the artifact file to `run_dir / "artifact.<ext>"`.
- Writes `result.json` to `run_dir / "result.json"` containing keys `last_run`, `success`, `artifact_path`.
- Updates the `~/Claude/<slug>/latest.json` symlink (atomic replace) to point at the new `result.json`.

Emit the snippet inside a single fenced `python` block (triple-backticks) inside `instrumentation-snippet.md`. Include a one-paragraph header naming the target skill slug and the artifact extension.

### Step 7 — Write instrumentation-snippet.md

Write the generated snippet to `instrumentation-snippet.md` in the phase directory. Do NOT also write it to `output.md` yet — `output.md` is the rationale wrapper and is written in Step 9.

### Step 8 — Run observability_lint

Run the lint on the generated snippet:

```bash
python3 scripts/observability_lint.py instrumentation-snippet.md
```

The lint returns JSON with `passed`, `fails`, `warns`, `info`. Rules A, B, C, D are checked. Exit codes 0 (pass), 1 (fail), 2 (bad usage).

**If `passed: true`:** continue to Step 9.

**If `passed: false` (first attempt):** apply the fix suggested by each `fails` entry. Re-run Step 6. Re-run the lint.

**If `passed: false` (second attempt):** write `BLOCKER: observability_lint failed twice; see fails[] for details` to `notes.md`. Do NOT overwrite `instrumentation-snippet.md` with a broken version. STOP. Human inspects per BP-028.

### Step 9 — Assemble output.md rationale

Write `output.md` with:
- A header naming the target skill slug.
- The snippet re-embedded from `instrumentation-snippet.md`.
- A short `## Rationale` section: one sentence per rule (A, B, C, D) explaining how the snippet satisfies that rule.

### Step 10 — Write notes.md and stop

Write `notes.md`:
- If any lint `warns` surfaced, repeat them as informational observations.
- If nothing noteworthy, write a one-line confirmation: `lint passed; 4/4 rules satisfied`.

STOP. Task complete.

## Self-test

The skill ships with three fixtures under `fixtures/`:

**Passing input (spec-driven):**
```
/skill-cron-observability fixtures/passing-input.md
```
Expected: `instrumentation-snippet.md` contains a correctly instrumented Python block; lint returns `passed: true`; matches `fixtures/expected-passing.md`.

**Passing snippet (already-written snippet, lint-only mode):**
```
python3 scripts/observability_lint.py fixtures/passing-snippet.md
```
Expected: `passed: true`, 0 fails.

**Gaps input:**
```
/skill-cron-observability fixtures/gaps-input.md
```
Expected: `notes.md` contains a `BLOCKER:` line; no `instrumentation-snippet.md` (or snippet missing the `latest.json` symlink). Matches `fixtures/expected-gaps.md`.

## Patterns enforced

- **BP-022** — cron/scheduled skills expose last-run, success, artifact location.
- **BP-021** — output home is `~/Claude/<skill>/` (not scattered across `/tmp` or `$HOME`).
- **BP-028** — `BLOCKER:` convention when self-lint fails twice or input preconditions violated.
- **BP-033** — read only `input.md`, never open `patterns/` directly.

## What to do if you're stuck

- **`input.md` missing** → write `BLOCKER: input.md not found at <path>` to `notes.md`. Do not guess.
- **Scheduling section missing cron frequency or artifact extension** → `BLOCKER: Scheduling section missing cron frequency or artifact extension`. Spec must declare both.
- **`is_scheduled: false` in the pack** → `BLOCKER: skill-cron-observability invoked but is_scheduled is false — driver bug`. This sub-skill must not run on non-scheduled skills.
- **Two lint failures in a row** → `BLOCKER:`. Let a human inspect.

## Why this skill is strict

A cron skill without observability is invisible until it breaks — debugging requires log archaeology, and by then the artifact is lost. The BP-022 contract is three files and one symlink; a mechanical lint catches missing fields that an eyeball review misses (the snippet wrote `result.json` but forgot `latest.json`, or stored `artifact_path` as a `Path` object instead of a string). Strict self-lint with forced BLOCKER on two failures is cheaper than a silent cron that nobody notices has been dead for weeks.
