# `skill-compliance-gate` invocation contract

Phase-scoped reference for Phase 8b (the compliance gate step). Cited by
`../director.md` Step B and Step C.

## Why the gate's `input.md` is narrower

Every other factory sub-skill consumes a standard `input.md` containing:

- `## Task` — one-line task statement.
- `## Spec excerpt` — H3-keyed sections from the client spec.
- `## Classified traits` — the 5 trait verdicts.
- `## BPs to enforce` — absolute paths to the BP files the sub-skill must read.
- `## Output locations` — where to write outputs.

The gate doesn't author content from a spec — it verifies an already-assembled
tree. So the gate's pack carries only:

- `## Task` — kept for parser symmetry.
- `## Assembled skill` — two `- **key**: value` lines:
  - `assembled_skill_path` — absolute path to `<work>/assembled/<slug>/`.
  - `work_dir` — absolute path to the factory work directory (used to
    locate `phases/08-assemble-and-gate/` for writing outputs).
- `## Output locations` — kept for parser symmetry.

No spec excerpt, no classified traits, no BPs. The gate's BPs are hardcoded
in `compliance_check.py` (Family 1, 13 checks) plus `gate.py` (Family 2,
Check 14 — meta-BP citation scan).

This is BP-033-compliant: the gate still reads ONLY its `input.md`. The
schema is just narrower than the standard.

## Why the positional CLI args are `/dev/null`

The driver invokes the pack builder with the standard 4-arg positional
form for parser symmetry:

```bash
python3 .../build_context_pack.py \
    /dev/null /dev/null skill-compliance-gate \
    <work>/phases/08-assemble-and-gate \
    --assembled-skill-path <work>/assembled/<slug> \
    --work-dir <work>
```

The first two positional args (`<spec-path>` and `<classifier-json>`) are
unused for the gate target. `/dev/null` is a clean sentinel that the gate's
build branch skips before any file-existence check would reject it.

This keeps the CLI's argparse-free positional grammar simple — there's no
gate-specific subcommand. A future refactor could promote the gate to a
proper subcommand if multiple no-spec sub-skills land.

## Spawning the gate Agent

Standard 5-step convention per `../../references/spawn-subagent.md`. The
only gate-specific notes:

- The gate writes EITHER `output.md` (PASS) OR `notes.md` (FAIL) — never
  both. The director's Step D checks `notes.md` first; if absent or empty
  of `BLOCKER:`, the verdict is PASS.
- The gate's BLOCKER line format is canonical:

  ```
  BLOCKER: compliance gate failed — <N> required-tier check(s) failed: <list>; <M> Check 14 meta-BP citation(s): <file:line (matched)>[, ...]
  ```

  The driver copies this verbatim to `<work>/notes.md` and STOPs. Do NOT
  reformat or summarize; the precise check IDs are debugging signal.

## Double-failure handling

Per the gate's own SKILL.md Step 5: do NOT re-run the gate after a FAIL.
Unlike content generators (frontmatter, phase-designer, signed-handoff),
the gate is a lint — a second invocation on the same input cannot change
the verdict. The user fixes the upstream cause (usually the spec) and
re-runs the factory from the top.
