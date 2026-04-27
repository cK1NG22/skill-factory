---
name: skill-compliance-gate
description: Factory-driven, hands-off compliance gate over a fully assembled skill directory. Runs the 13-check skill-compliance audit via subprocess and adds Check 14 (no `patterns/meta/bp-*` citations in a client skill). Use when "run the compliance gate", "gate the assembled skill", "check 14 meta citation scan", "skill-compliance-gate <path>", or when the skill-factory driver invokes this in Phase 8 as the universal closure step. Do NOT use for interactive audits (use `/skill-compliance` instead); this gate is silent, binary, and BLOCKERs on BP-028.
argument-hint: "<phase-input-md-path | --skill assembled-dir>"
allowed-tools:
  - Read
  - Bash
  - Write
---

# skill-compliance-gate

**Read ONLY your driver-supplied `input.md`** (per BP-033). The driver materializes it under `phases/08-assemble-and-gate/input.md` (Stage 10b wiring; the path is also embedded in your invocation prompt). The pack declares two fields: `assembled_skill_path` (absolute path to the directory Phase 8a assembled) and `work_dir` (the factory workspace root, used only to locate the phase directory for writing notes/output).

The one thing this skill produces: a pass/fail verdict over the assembled skill directory, written to `phases/08-assemble-and-gate/{notes.md | output.md}`. On PASS, `output.md` contains a tidy summary table. On FAIL, `notes.md` contains a `BLOCKER:` line naming the failed checks; `output.md` is not written.

## What this skill does NOT do

- Does NOT audit a live skill tree under `~/.claude/skills/` wholesale — use `/skill-compliance --all` for that.
- Does NOT ask the user questions — factory-driven, hands-off per BP-026.
- Does NOT fix anything it finds — reports only. Fixes come from re-running the factory against a corrected spec.
- Does NOT duplicate `compliance_check.py`'s 13 checks — it subprocess-calls the canonical script at `~/.claude/skills/skill-compliance/scripts/compliance_check.py` and parses its JSON.
- Does NOT author any part of the assembled skill — that is `assemble_skill.py`'s job (Phase 8a).

## Trigger logic

This sub-skill fires on every factory run — there is no trait gate. Phase 8 (assemble + gate) is the universal closure step per `phase-spine.md`.

## Invocation modes

### Driver-invoked (normal case)

Called as an isolated `Agent` subtask from the Skill Factory driver's Phase 8 (Stage 10b wiring).

**Reads:**
- `phases/08-assemble-and-gate/input.md` — the driver-materialized context pack. Contains `assembled_skill_path` and `work_dir`.

**Writes (to `phases/08-assemble-and-gate/`):**
- `output.md` — summary table on clean PASS.
- `notes.md` — `BLOCKER:` line on FAIL, otherwise short informational observations.

### Standalone (manual)

```
python3 scripts/gate.py --skill <path-to-assembled-skill-dir>
```

Standalone mode prints JSON to stdout and exits 0 (pass) or 1 (fail); no files are written. Used by the test suite and for one-off manual runs against fixtures.

## Procedure

Follow these steps in order.

### Step 1 — Load the input pack

Read `input.md`. The pack contains:
- **assembled_skill_path** — absolute path to the Phase-8a-assembled skill directory.
- **work_dir** — the factory workspace root; `phases/08-assemble-and-gate/` lives directly underneath.

If either field is missing or points at a non-existent path, write `BLOCKER: skill-compliance-gate input.md is malformed — field <name> missing` (or `... points to missing path <p>`) to `notes.md` and STOP.

### Step 2 — Confirm the checker core is reachable

Verify `~/.claude/skills/skill-compliance/scripts/compliance_check.py` exists. If the path is missing, write `BLOCKER: skill-compliance not installed at <path>` to `notes.md` and STOP. See `references/gate-contract.md` for why this is a hard precondition.

### Step 3 — Run gate.py

Run the gate orchestrator:

```bash
python3 scripts/gate.py --input <path-to-input.md>
```

`gate.py` performs three actions, in order:
1. Subprocess-call the checker core against `assembled_skill_path` and parse its JSON.
2. Run Check 14 (meta-BP citation scan) against the assembled skill's `SKILL.md`, `references/` tree (one level deep per BP-008), and `phases/*/director.md` + `phases/*/references/` (when present).
3. Aggregate: any required-severity FAIL from the checker OR any Check 14 hit → overall FAIL.

### Step 4 — Write the verdict

Read the verdict file `gate.py` already wrote — either `output.md` (PASS) or `notes.md` (FAIL) under the phase directory extracted from `input.md`. Confirm the contents match the verdict:
- PASS → `output.md` exists with the summary table. STOP. Task complete.
- FAIL → `notes.md` contains a `BLOCKER:` line naming every failed check (required-tier FAILs + Check 14 hits). STOP. Driver STOPs before Phase 99 per BP-028.

### Step 5 — Double-failure handling

Do not re-run `gate.py` after a FAIL. Unlike generators (frontmatter, phase-designer, signed-handoff), the gate is a lint — a second attempt would not change the verdict. The BLOCKER line in `notes.md` is the authoritative signal.

## Self-test

The skill ships with three fixture scenarios under `fixtures/`:

**Passing:**
```
python3 scripts/gate.py --skill fixtures/passing
```
Expected: exit 0, JSON reports `verdict: "pass"`, zero check-14 hits.

**Failing-required:**
```
python3 scripts/gate.py --skill fixtures/failing-required
```
Expected: exit 1, JSON reports `verdict: "fail"`, at least one required-tier check from the checker core in the fail list (the fixture has an empty `description` field).

**Failing-meta-cite:**
```
python3 scripts/gate.py --skill fixtures/failing-meta-cite
```
Expected: exit 1, JSON reports `verdict: "fail"`, at least one Check 14 hit on `bp-028` or `patterns/meta/bp-028` inside the fixture's `references/` tree.

## Patterns enforced

- **BP-025** — sibling skills, not nested. `skill-compliance-gate` is a sibling of `skill-compliance`, not a mode under it.
- **BP-026** — sole human touchpoint is the spec author; the gate is hands-off (no AskUserQuestion).
- **BP-028** — BLOCKER convention on gate FAIL; driver STOPs before Phase 99.
- **BP-031** — co-locate co-evolving tools. `compliance_check.py` stays canonical in `skill-compliance/scripts/`; the gate subprocess-calls it rather than duplicating the 13-check logic.
- **BP-033** — read only `input.md`; do not open the spec file or `patterns/` directly.
- **BP-034** — the gate is cross-skill reuse of `compliance_check.py`, which is exactly the case BP-034 authorizes a sub-skill for.

## What to do if you're stuck

- **`input.md` missing** → `BLOCKER: input.md not found at <path>`. Do not guess.
- **`assembled_skill_path` points at a non-existent directory** → `BLOCKER: assembled skill not found at <path>`. Phase 8a's assembly step failed silently; surface it.
- **`compliance_check.py` not at the expected path** → `BLOCKER: skill-compliance not installed at <path>`. The gate has a hard runtime dependency on the sibling skill-compliance sub-skill.
- **Checker core returns non-JSON output** → `BLOCKER: compliance_check.py returned unparseable output — <first line of stderr>`. Do not guess at the verdict.

## Why this gate exists

Before Stage 10b, the factory produced a pile of per-phase outputs under `<work>/phases/NN-*/output.*` and stopped. Nothing assembled them into a skill directory; nothing verified that the assembled directory would pass the 13-check audit. That meant every factory run needed a manual compliance pass before the authored skill could ship.

The gate closes the loop: every factory run now produces either a fully compliant assembled skill directory, or a hard BLOCKER naming what's wrong. No intermediate state. No silent drift. The sole human touchpoint stays at the spec-authoring stage (BP-026).
