---
name: skill-signed-handoff
description: Generate a signed-handoff signature script for a factory-authored pipeline skill whose traits fire 'has_phases' AND 'invokes_skills'. Use when "generate signature script", "sign the handoff", "wire up signed handoff", "stamp the deck_signature", "emit sha256 signature script", "skill-signed-handoff <workspace>", or when the skill-factory driver invokes this in Phase 4 because both has_phases and invokes_skills fire. Do NOT use for single-skill signatures, auth tokens, or cryptographic key exchange — this is an integrity check over named fields within one agent session (BP-024).
argument-hint: "<phases-dir-or-input-md-path>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-signed-handoff

**Read ONLY your driver-supplied `input.md`** (per BP-033). The driver materializes it under `phases/07-skill-signed-handoff/input.md` (Stage 9b wiring; the path is also embedded in your invocation prompt). The pack has distilled the spec's "Existing skills to reuse" section, the terminal-upstream and entry-downstream phase identifiers, the argument-bearing field list, and the specific BP file paths. Do NOT open the `patterns/` directory directly. Do NOT open the full spec file directly.

The one thing this skill produces: a `<skill-slug>_signature.py` script that passes `scripts/handoff_lint.py` against `references/signed-handoff-rules.md`, stamped from `scripts/signature-template.py` with the target skill's SIGNED_FIELDS list.

## What this skill does NOT do

- Does NOT author the SKILL.md frontmatter (that is `skill-frontmatter`'s job).
- Does NOT author the `## Procedure` section (that is `skill-phase-designer`'s job).
- Does NOT wire `references/` scaffolding (that is `skill-references-scaffolder`'s job).
- Does NOT invent a field list that is not declared in the spec's reuse section.

## Trigger logic

This sub-skill fires only when the classifier's trait verdicts have BOTH `has_phases: true` AND `invokes_skills: true`. Per BP-024, that intersection is the "pipeline orchestrator" case; no dedicated trait exists. If either trait is `false` in the pack, the skill stops immediately — see Step 1.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 7 (Stage 9b wiring; AND-gated on `has_phases ∧ invokes_skills`).

**Reads:**
- `phases/07-skill-signed-handoff/input.md` — the driver-materialized context pack.

**Writes (to `phases/07-skill-signed-handoff/`):**
- `output-signature-template.py` — the stamped signature script ready to drop into the target skill's `scripts/` directory.
- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations (declared fields, upstream/downstream phase bindings).

### Standalone (manual)

```
/skill-signed-handoff <path-to-input.md-or-its-parent-dir>
```

## Procedure

Follow these steps in order.

### Step 1 — Load the input pack

Read `input.md`. The pack contains:
- **Task** — a one-line statement.
- **Spec excerpt** — the "Existing skills to reuse" section, the upstream skill's argument-bearing-fields list, and the entry/terminal phase identifiers for the downstream and upstream sides of the handoff.
- **Classified traits** — the 5 trait verdicts from Phase 2. Only `has_phases` and `invokes_skills` gate this sub-skill.
- **BPs to enforce** — absolute paths to BP files. Always BP-024. Also BP-028 and BP-033.
- **Output locations** — where to write `output-signature-template.py` and `notes.md`.

If `has_phases` or `invokes_skills` is not `true` in the pack, write `BLOCKER: skill-signed-handoff invoked but has_phases ∧ invokes_skills is false — driver bug` to `notes.md` and STOP.

### Step 2 — Load the rules contract

Read `references/signed-handoff-rules.md`. This is the authoritative source for Rules A–F.

### Step 3 — Read the listed BP files

For each `patterns/bp-NNN-*.md` path listed under "BPs to enforce", read the file. Do NOT read BP files not listed.

### Step 4 — Extract the signed-fields list

Parse the spec excerpt's "argument-bearing fields" section (or the equivalent "signed fields" / "handoff fields" heading):
- If the section is missing or lists zero fields, write `BLOCKER: spec declares no argument-bearing fields; signed handoff is meaningless without them` to `notes.md` and STOP.
- If the section lists one or more fields, capture them as a Python string-list literal. Preserve the spec's ordering — the lint sorts at serialization time but declared ordering helps review.

### Step 5 — Bind the skill slug and phase identifiers

Extract the upstream skill slug (the skill whose terminal phase writes the signature). Derive the output script filename as `<slug>_signature.py`. Capture the terminal-phase identifier (e.g., `phase-6`) and the downstream entry-phase identifier (e.g., `phase-1`) for the notes file.

### Step 6 — Load the signature template

Read `scripts/signature-template.py`. The template already includes argparse plumbing for `--sign` / `--verify`, a `compute_signature` helper that hashes the canonical JSON, and the four exit codes. The only substitutions are the module docstring's `{skill_slug}` placeholder and the `SIGNED_FIELDS` list literal body.

### Step 7 — Stamp the template

Apply two substitutions to the template text in memory:
- Replace every `{skill_slug}` placeholder with the captured slug.
- Replace the default `SIGNED_FIELDS = [...]` block with the list from Step 4, one field per line with trailing commas and the existing indentation.

Do NOT alter the argparse wiring, the canonical-serialization call, or the exit-code returns. The template already satisfies Rules A–F; the stamping only parameterizes the fields.

### Step 8 — Write the stamped script

Write the in-memory text to `output-signature-template.py` in the phase workspace directory. Use UTF-8 encoding with a trailing newline.

### Step 9 — Self-lint

Run the lint:

```bash
python3 scripts/handoff_lint.py output-signature-template.py
```

The lint returns JSON with `passed`, `fails`, `warns`, `info`.

**If `passed: true`:** write `notes.md` with the declared SIGNED_FIELDS list, the upstream/downstream phase bindings, and any lint `warns` repeated as informational observations. STOP. Task complete.

**If `passed: false` (first attempt):** apply the fix suggested by each `fails` entry. Re-run Steps 7–8 as needed. Re-run the lint.

### Step 10 — Escalate on double failure

If the lint still reports `passed: false` after the second attempt, write `BLOCKER: handoff_lint failed twice; see fails[] for details` to `notes.md`. Do NOT overwrite `output-signature-template.py` with a broken version. STOP. Human inspects per BP-028.

## Self-test

The skill ships with two fixture scenarios under `fixtures/`:

**Passing:**
```
/skill-signed-handoff fixtures/passing-input.md
```
Expected: `output-signature-template.py` is a clean stamped script with three declared fields; lint returns `passed: true`. A reference copy lives at `fixtures/passing-signature-script.py` for byte-level comparison.

**Gaps:**
```
/skill-signed-handoff fixtures/gaps-input.md
```
Expected: `notes.md` contains a `BLOCKER:` line; `output-signature-template.py` is either absent or still contains the unstamped placeholder. Matches `fixtures/expected-gaps.md`.

## Patterns enforced

- **BP-024** — signed handoffs between pipeline skills (sha256 over argument-bearing fields).
- **BP-028** — `BLOCKER:` convention when self-lint fails twice or input preconditions are violated.
- **BP-033** — read only `input.md`, never open `patterns/` directly.

## What to do if you're stuck

- **`input.md` missing** → write `BLOCKER: input.md not found at <path>` to `notes.md`. Do not guess.
- **Spec declares no argument-bearing fields** → `BLOCKER: spec declares no argument-bearing fields; signed handoff is meaningless without them`. The spec-validator should have caught this earlier; surface it.
- **Either `has_phases` or `invokes_skills` is false** → `BLOCKER: skill-signed-handoff invoked but has_phases ∧ invokes_skills is false — driver bug`. This sub-skill must not run outside that intersection.
- **Two lint failures in a row** → `BLOCKER:` per Step 10. Let a human inspect.

## Why this skill is strict

A signed handoff is the trust boundary between two cooperating skills. A signature script with a missing `--verify` mode or a non-canonical serialization produces mismatches that LOOK like corrupted payloads but are really bugs in the signing tool — the downstream skill blames the upstream, engineers waste a day. The deterministic lint catches all six structural problems (missing modes, wrong hash, empty fields, missing exit codes, unsorted serialization) before the script ever runs. Strict self-lint with forced BLOCKER on two failures is cheaper than a handoff that silently drifts in production.
