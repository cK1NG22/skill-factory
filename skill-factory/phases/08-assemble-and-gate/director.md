# Phase 8 — assemble + compliance gate (always fires)

Phase 8 is the universal closure step of the factory loop. It runs on every
factory run regardless of which traits fired upstream — there is no trait
gate (Pattern A / B / C all skip this phase).

Phase 8 does two things, in order:

1. **Assemble** the per-phase outputs at `<work>/phases/NN-*/` into a single
   skill directory at `<work>/assembled/<slug>/`. Run by the inline
   `scripts/assemble_skill.py` (no sub-skill — assembly is mechanical).
2. **Gate** the assembled directory by spawning the `skill-compliance-gate`
   sub-skill as an isolated Agent subtask. The gate verifies the assembled
   tree against the canonical 13-check audit (Family 1) plus the meta-BP
   citation scan (Check 14, Family 2).

On a clean PASS, Phase 99 (report) fires. On a FAIL, the driver STOPs before
Phase 99 per BP-028 — the BLOCKER line in `notes.md` is the authoritative
signal to the user.

## Procedure

### Step A — Assemble the skill directory

Run `assemble_skill.py` against the work directory:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/assemble_skill.py \
    <work>
```

Exit codes:
- 0 → assembled directory is at `<work>/assembled/<slug>/`. The script prints
  the absolute path on stdout. Continue to Step B.
- 1 → required phase output missing. Write
  `BLOCKER: assembly failed — <stderr>` to `<work>/notes.md` and STOP.
- 2 → malformed phase output. Write
  `BLOCKER: assembly failed — <stderr>` to `<work>/notes.md` and STOP.

`assemble_skill.py` reads `<work>/classifier.json` to know which optional
phases fired and pulls phase outputs accordingly. See
`references/assembly-contract.md` for the per-phase output → assembled-file
mapping plus the ASSEMBLY-MANIFEST.json schema.

### Step B — Materialize the gate's input pack

The gate's input.md schema is intentionally narrower than every other
sub-skill — it carries only `assembled_skill_path` and `work_dir`:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/build_context_pack.py \
    /dev/null /dev/null skill-compliance-gate \
    <work>/phases/08-assemble-and-gate \
    --assembled-skill-path <work>/assembled/<slug> \
    --work-dir <work>
```

The positional `<spec-path>` and `<classifier-json>` are unused by the gate
target — `/dev/null` is a clean sentinel. See
`references/gate-invocation.md` for why the schema is minimal.

### Step C — Spawn `skill-compliance-gate`

Spawn the gate as an isolated Agent subtask per
`../../references/spawn-subagent.md` (the standard 5-step convention).
Pass the exact `input.md` path produced in Step B.

The gate writes one of two file pairs into
`<work>/phases/08-assemble-and-gate/`:

- On PASS → `output.md` (summary table) only.
- On FAIL → `notes.md` with a single `BLOCKER:` line naming every failed
  required-tier check and every Check 14 hit.

### Step D — Interpret the verdict

Read `<work>/phases/08-assemble-and-gate/notes.md`. If the file exists AND
its first non-empty line begins with `BLOCKER:`, copy that line verbatim
to `<work>/notes.md` and STOP. Do NOT enter Phase 99.

If `notes.md` does not exist (gate didn't write one) OR contains only
informational observations, read `output.md` to record the gate verdict
and continue to Step 9 (Phase 99 — report). The report should announce
"compliance gate: PASS" alongside the assembled-directory path.

## What this phase does NOT do

- Does NOT install the assembled skill to `~/.claude/skills/`. That is a
  post-factory step the user takes manually (or via a future Stage 11).
- Does NOT auto-fix gate failures. On FAIL, the driver STOPs and the user
  re-runs the factory against a corrected spec per BP-026.
- Does NOT retry the gate. Unlike generators (frontmatter, phase-designer,
  signed-handoff), the gate is a lint — a second attempt cannot change the
  verdict without an upstream change.

## Cross-reference

- Per-phase output → assembled-file mapping (BP-031 contract):
  `references/assembly-contract.md`.
- Why the gate's input.md is narrower than other sub-skills (BP-033 still
  satisfied): `references/gate-invocation.md`.
- Agent-spawn mechanics (BP-023): `../../references/spawn-subagent.md`.
- BLOCKER convention on gate FAIL (BP-028):
  the gate emits the canonical BLOCKER line; the driver STOPs.
