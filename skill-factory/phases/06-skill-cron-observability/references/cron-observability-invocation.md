# skill-cron-observability invocation contract (phase-scoped)

Phase-scoped reference for Phase 6. Cited by `../director.md`.

## Pack shape

`build_context_pack.py <spec> <classifier.json> skill-cron-observability
<out-dir>` materializes `input.md` with these sections:

1. **`# Task`** — "Generate a BP-022-compliant instrumentation snippet
   for the target cron skill."
2. **`## Spec excerpt`** — base sections: `Company`, `Skill slug`,
   `One-line description`, `Inputs`, `Outputs`, `Scheduling`,
   `Happy-path walkthrough`, `Failure modes`. The `Scheduling` body
   carries the cron expression and artifact extension.
3. **`## Classified traits`** — the 5 traits.
4. **`## BPs to enforce`** — base is BP-022 (cron observability) +
   BP-021 (output home). No trait-gated additions.
5. **`## Output locations`** — `instrumentation-snippet.md`,
   `output.md`, `notes.md`.

## BP-set breakdown

Always applied (base, fired by `is_scheduled`):
- **BP-022** — Cron/scheduled skills expose last-run timestamp,
  success flag, and artifact location via the `result.json` /
  `latest.json` contract.
- **BP-021** — Output home is `~/Claude/<skill>/` (canonical path
  shape; not `/tmp` or `$HOME` directly).

There are NO trait-gated additions for skill-cron-observability. Any
scheduled skill — phased or flat, HITL or unattended — applies the
same BP-022 contract. The base list is the whole list.

## Lint flags the driver passes

None. `observability_lint.py` takes a single positional argument: the
path to the snippet file (or scripts directory) to lint. No flags.

## BLOCKER causes

- **Scheduling section missing** the cron frequency or artifact
  extension. Spec must declare both. Sub-skill BLOCKERs at its own
  Step 4.
- **Two consecutive lint failures** on the generated snippet — sub-
  skill internally retries once, then BLOCKERs per BP-028.
- **`is_scheduled: false`** in the pack — never happens via the
  driver (entry gate prevents it), but the sub-skill defends against
  the case for direct invocation.

## instrumentation-snippet.md shape the driver reads

A single fenced ` ```python ` block containing the four required
operations:
1. `timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")`
2. `run_dir = Path("~/Claude/<slug>/runs/") / timestamp` + `mkdir(...)`
3. Write `result.json` with `last_run`, `success`, `artifact_path`
   keys, and the artifact file alongside.
4. Atomic-replace `~/Claude/<slug>/latest.json` to point at the new
   `result.json`.

The driver hands the snippet to Phase 99 as-is; the user pastes it
into the target skill's `scripts/<entrypoint>.py`.

## output.md vs instrumentation-snippet.md

Two artifacts, both written by the sub-skill:
- **`instrumentation-snippet.md`** — the bare snippet, ready to paste.
  Lint reads this file.
- **`output.md`** — rationale wrapper: the snippet re-embedded plus
  one sentence per BP-022 rule (A–D) explaining how the snippet
  satisfies it. This is for human review, not for downstream tooling.
