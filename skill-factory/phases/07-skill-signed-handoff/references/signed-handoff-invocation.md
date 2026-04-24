# skill-signed-handoff invocation contract (phase-scoped)

Phase-scoped reference for Phase 7. Cited by `../director.md`.

## Pack shape

`build_context_pack.py <spec> <classifier.json> skill-signed-handoff
<out-dir>` materializes `input.md` with these sections:

1. **`# Task`** — "Stamp a `<slug>_signature.py` script for the
   upstream skill's terminal phase, signing the argument-bearing
   fields declared in the spec."
2. **`## Spec excerpt`** — base sections: `Company`, `Skill slug`,
   `One-line description`, `Existing skills to reuse`, `Happy-path
   walkthrough`, `Failure modes`, plus two custom optional sections
   when the spec declares them: `Pipeline composition` (upstream /
   downstream phase identifiers) and `Argument-bearing fields` (the
   signed-fields list).
3. **`## Classified traits`** — the 5 traits.
4. **`## BPs to enforce`** — only BP-024 (signed handoffs). Meta BPs
   (BP-028, BP-033) are factory-internal discipline the sub-skill
   self-applies via its own SKILL.md — not shipped in the pack
   (consistent with frontmatter / phase-designer / cron / refs).
5. **`## Output locations`** — `output-signature-template.py`,
   `notes.md`.

## BP-set breakdown

Always applied (base, fired when `has_phases ∧ invokes_skills`):
- **BP-024** — Signed handoffs between pipeline skills (sha256 over
  argument-bearing fields, canonical JSON serialization with
  `sort_keys=True`, four reachable exit codes 0/1/2/3).

There are NO trait-gated additions for skill-signed-handoff. The
trigger is itself an AND of two traits, so further gating is
redundant. The base list is the whole list.

## Lint flags the driver passes

None. `handoff_lint.py` takes a single positional argument: the path
to the stamped signature script. No flags.

## BLOCKER causes

- **Either `has_phases` or `invokes_skills` is false** — never reaches
  this phase via the driver (the `--should-fire` gate prevents it),
  but the sub-skill defends against the case for direct invocation.
- **Spec declares no argument-bearing fields** — the `Argument-bearing
  fields` section is empty or missing. Sub-skill BLOCKERs at its own
  Step 4. Fix upstream: spec must declare the signed-field list.
- **Two consecutive lint failures** on the stamped script — sub-skill
  internally retries once, then BLOCKERs per BP-028.

## output-signature-template.py shape the driver reads

A standalone Python script (no external dependencies) that:
- Has `--sign <payload-json> <signature-out>` and
  `--verify <payload-json> <signature-in>` argparse modes.
- Imports `hashlib` and uses `hashlib.sha256` over
  `json.dumps(canonical_payload, sort_keys=True)`.
- Declares a top-level `SIGNED_FIELDS` list literal with the spec's
  declared field names (one per line, preserving spec order).
- Returns reachable `sys.exit(0|1|2|3)` for ok / mismatch /
  missing-field / bad-usage.

The driver hands the script to Phase 99 as-is; the user drops it
into the target skill's `scripts/<slug>_signature.py`.
