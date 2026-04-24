# pipeline-deck (narrow-signed-handoff spec)

Stage 9b fixture. Designed to fire **only** `has_phases` + `invokes_skills`
(the AND-intersection that triggers signed-handoff). No Reference
exemplars, no Scheduling section, no HITL prompts. Walkthrough is
numbered (5 items) so `has_phases` fires; reuse section names `/pptx`
so `invokes_skills` fires.

## Company

acme

## Skill slug

pipeline-deck

## One-line description

Builds a `.pptx` deck downstream of `/pptx`, verifying the upstream signature before consuming any spec field. Use when "build pipeline deck", "downstream deck from case", "verify signed deck spec".

## Trigger phrases

- build pipeline deck
- downstream deck from case
- verify signed deck spec
- run pipeline-deck
- generate the deck from the case spec

## Inputs

- A signed deck-spec JSON written by `/pptx`'s terminal phase to `<work>/upstream/spec.json`.
- A signature file written alongside it at `<work>/upstream/spec.json.sig`.

## Outputs

- A finalized `.pptx` deck at `<work>/output/deck.pptx`.
- A run log at `<work>/output/run.log` documenting the verify-then-build sequence.

## Happy-path walkthrough

1. Read `<work>/upstream/spec.json` and `<work>/upstream/spec.json.sig` from disk.
2. Run `python3 scripts/pipeline-deck_signature.py --verify <work>/upstream/spec.json <work>/upstream/spec.json.sig`. On exit 0, proceed to step 3. On any non-zero exit, abort with `BLOCKER: upstream signature did not verify` written to `<work>/output/run.log` and stop.
3. Parse the verified spec into structured deck sections (cover, argument flow, leadlines, recommendation).
4. Render the deck via `python3 scripts/build_deck.py --in <verified-spec> --out <work>/output/deck.pptx`.
5. Write the run log and exit cleanly.

## Success signals

- The signature verification step completes with exit code 0 against the upstream signature.
- The output `.pptx` opens cleanly in PowerPoint and contains exactly four section headers (cover, argument flow, leadlines, recommendation).
- The run log documents the verified spec hash and the deck artifact path.

## Failure modes

- **Upstream signature does not verify** → abort the entire run; do NOT consume the spec; write `BLOCKER:` to run.log and stop.
- **Deck rendering raises an exception** → write the exception trace to run.log; do NOT produce a partial `.pptx`.
- **Either input file is missing** → write `BLOCKER: missing upstream artifact at <path>` to run.log and stop.

## Existing skills to reuse

- `/pptx` — the upstream pipeline producer. Writes the deck spec in its own terminal phase. This skill verifies the signature before consuming any field.

## Pipeline composition

- **Upstream:** `/pptx` writes the deck spec in its terminal phase (phase-6). The terminal phase also runs `pptx_signature.py --sign` to produce the signature file.
- **Downstream:** this skill (`pipeline-deck`) reads the spec in its entry phase (phase-1) and MUST verify the signature before consuming any spec field.

## Argument-bearing fields

The handoff contract signs the following fields of the deck spec:

- `argument_flow`
- `leadlines`
- `recommendation`
