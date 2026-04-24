# strategy-coach (narrow-refs-only spec)

Stage 9a fixture. Designed to fire **only** the `has_references` trait
in the classifier. Walkthrough uses bulleted prose (no numbered list
items) to avoid `has_phases` firing. No Scheduling, no `/<skill>` reuse,
no HITL prompts.

## Company

acme

## Skill slug

strategy-coach

## One-line description

Asks scoped intake questions, then surfaces strategy frameworks and known anti-patterns from a curated reference library. Use when "strategy coach", "scope my project", "which framework should I use".

## Trigger phrases

- strategy coach
- scope my project
- which framework should I use
- run strategy coach
- coach me on strategy

## Inputs

- The user's project description, supplied as a prose paragraph.

## Outputs

- A scoping summary in `output.md` covering scope clarifications, recommended frameworks, and anti-patterns to watch.

## Happy-path walkthrough

The agent reads the scoping-questions reference and asks the four highest-priority questions in a single message, surfacing each one as a numbered question per BP-015. After the user replies, the agent reads the frameworks-overview reference and selects the framework that best matches the project shape; the agent never proposes a framework before reading this reference. Finally, the agent reads the anti-patterns reference and flags any anti-pattern hits in the user's response, calling out which intake-question answer triggered the flag.

## Success signals

- The user receives a one-paragraph scope clarification that names two or more constraints they had not previously articulated.
- The recommended framework includes a one-line "why this fits" explanation that cites at least one of the user's stated inputs.
- Any flagged anti-pattern is paired with a concrete remediation step, not just a warning label.

## Failure modes

- **User skips the intake reply** → the agent re-asks the four scoping questions once, then writes `BLOCKER: user did not respond to intake; cannot recommend a framework without scope` to `notes.md` and stops.
- **No framework matches the project shape** → the agent writes `BLOCKER: no framework in frameworks-overview matches the user's described project; library may need expansion` to `notes.md`. Does not invent a framework.
- **Reference file unreachable** → the agent writes `BLOCKER: could not read references/<name>.md; check the references/ folder is populated` and stops.

## Existing skills to reuse

None.

## Reference exemplars

- `scoping-questions.md` — the canonical list of 12 intake questions, ordered by impact-on-recommendation. Loaded before the first user prompt.
- `frameworks-overview.md` — a one-line description per supported framework (Porter Five Forces, JTBD, Wardley Map, etc.) plus "fits when..." selectors.
- `anti-patterns.md` — eight common strategy-doc anti-patterns with the user-input signal that triggers each.

## Anti-goals

- Does NOT generate the strategy doc itself; only scopes and recommends. Doc generation is the user's job.
- Does NOT add reference files dynamically. The library is curated; new entries require a separate authoring pass.
