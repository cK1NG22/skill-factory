# weekly-ai-pipeline-digest (omnibus 5-trait spec)

Stage 9b crown stress-test fixture. Designed to fire **all 5 traits**
simultaneously — the maximum-load case for the factory driver. A single
`/skill-factory` run against this spec must produce 5 phase outputs
(frontmatter, phase-designer, references-scaffolder, cron-observability,
signed-handoff) plus the report.

Domain: a weekly digest of AI/ML pipeline health that runs on a cron,
walks a phased HITL review with the human, references a library of
prompt templates, and produces a signed `.docx` artifact downstream
to a `/pptx` slide builder.

## Company

acme

## Skill slug

ai-pipeline-digest

## One-line description

Compiles a weekly markdown + .docx digest of AI/ML pipeline health, runs an HITL review pass with the on-call engineer before publication, and signs the resulting deck spec for downstream consumption by the slide builder. Use when "weekly AI pipeline digest", "pipeline health report", "ai/ml status digest".

## Trigger phrases

- weekly AI pipeline digest
- pipeline health report
- ai/ml status digest
- run pipeline digest
- generate the weekly pipeline digest

## Inputs

- A configured list of pipeline definitions in `~/.config/ai-pipeline-digest/pipelines.yaml`. Read once per scheduled run.
- The on-call engineer's review responses, captured during the HITL pass.
- Prompt templates from the `references/` knowledge base — one reference file per rendered section (status summary, drift commentary, action items). Each reference file is a self-contained framework for that section's structure and tone.

## Outputs

- A weekly digest at `~/Claude/acme-ai-pipeline-digest/runs/<timestamp>/digest.docx`, produced via `/docx`.
- A deck spec at `~/Claude/acme-ai-pipeline-digest/runs/<timestamp>/deck-spec.json` that the downstream `/pptx` skill consumes.
- A signature file at `~/Claude/acme-ai-pipeline-digest/runs/<timestamp>/deck-spec.json.sig` produced by the stamped `ai-pipeline-digest_signature.py`.

## Happy-path walkthrough

1. The cron daemon fires the script at the scheduled time. The script reads `pipelines.yaml` and the prompt-template references (status-summary, drift-commentary, action-items) before any LLM call.
2. The script renders a draft digest section per pipeline, then pauses and asks the user to confirm each section's interpretation. Wait for the user's reply before proceeding to the next section.
3. After all sections are confirmed, the script asks the user to select the headline section that anchors the digest. The user chooses from the confirmed list.
4. The script assembles the full digest, hands it to `/docx` for `.docx` rendering, and writes the artifact alongside `result.json` per BP-022.
5. The script writes the deck spec JSON, runs `python3 scripts/ai-pipeline-digest_signature.py --sign deck-spec.json deck-spec.json.sig`, and then notifies the downstream `/pptx` orchestration channel that a new signed spec is available.

## Success signals

- A new `runs/<timestamp>/` directory contains `digest.docx`, `deck-spec.json`, and `deck-spec.json.sig` every Friday at 16:00 UTC.
- The user confirms every section without overrides; if the user requests an override on more than one section, the digest publishes anyway with override notes appended.
- The signature file verifies cleanly via `--verify` against `deck-spec.json` immediately after signing (sanity check before the channel notification).

## Failure modes

- **User does not respond within 30 minutes during the HITL pass** → the script writes `BLOCKER: user unresponsive during section review; digest aborted` to `notes.md` and stops without producing an artifact.
- **`/docx` rendering fails** → the script writes `BLOCKER: docx render failed; check the rendering library version` to `notes.md`, records `success: false` in `result.json`, and skips the signature step entirely.
- **Signature self-verification fails immediately after signing** → the script writes `BLOCKER: signature did not self-verify; signing tool is broken` and aborts before notifying the downstream channel.

## Existing skills to reuse

- `/docx` — renders the digest sections into a polished `.docx` file. Invoked once per run during the assembly step.
- `/pptx` — downstream consumer of the signed deck spec. The pipeline digest hands off; the slide-builder runs in its own session.

## Reference exemplars

- `status-summary-template.md` — prompt template for the status-summary section. Loaded once before the first LLM call per pipeline.
- `drift-commentary-template.md` — prompt template for the drift-commentary section. Includes the canonical KL-divergence threshold for flagging drift as a degradation event.
- `action-items-template.md` — prompt template for the action-items section. Defines the verb taxonomy (investigate / remediate / monitor / accept) the agent uses to label each item.

## Scheduling

- **Cron frequency:** `0 16 * * 5` (Fridays at 16:00 UTC).
- **Artifact extension:** `.docx`.
- **Skip overlapping runs:** if a previous Friday's run is still in flight (presence of an in-flight `runs/<timestamp>/.lock` file), the new run aborts cleanly with `success: false` and skips the digest.
- **HITL timeout:** 30 minutes per section confirmation. Beyond that, the script BLOCKERs (see Failure modes).

## Pipeline composition

- **Upstream:** none — this skill is the pipeline source. The cron run reads its inputs from local config + the live pipeline state.
- **Downstream:** `/pptx` consumes the signed `deck-spec.json` in its entry phase. The `/pptx` skill MUST verify the signature before consuming any spec field.

## Argument-bearing fields

The handoff contract signs the following fields of the deck spec:

- `pipeline_summaries`
- `drift_commentary`
- `action_items`
- `headline_section_id`
