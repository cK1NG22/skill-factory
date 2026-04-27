# Client Skill Spec — <replace-with-your-skill-slug>

<!--
  This is the Skill Factory's input form. Copy it, fill in each section,
  then run `/skill-spec-validator <path-to-your-copy>` before handing it
  to `/skill-factory`. Every REQUIRED section is authoritative: the
  factory will not author a skill from an incomplete or ambiguous spec.

  The form ships pre-filled with the minimum content that passes the
  validator, so you can run the validator on an unmodified copy as a
  smoke test. REPLACE the placeholder content — do not ship a skill
  named `your-skill-name` at company `your-company`.

  Rules live in `skill-spec-validator/references/spec-requirements.md`.
  Common failure modes are in `assets/spec-anti-patterns.md` — read that
  first if this is your first spec.
-->

## Company
<!--
  Lowercase letters, digits, and hyphens only. 2-32 chars.
  Becomes the folder name for the client's skill repo:
  `~/Projects/<company>-claude-skills/`.
  Examples: `acme`, `bravo-corp`, `contoso`.
-->
your-company

## Skill slug
<!--
  Short hyphenated identifier for the skill itself. 2-40 chars,
  lowercase letters, digits, and hyphens only.
  Use the bare skill name — no company prefix needed. Namespacing
  comes from the per-client repo at `~/Projects/<company>-claude-skills/`.
  Examples: `board-memo`, `onboarding-checklist`, `invoice-render`.
-->
your-skill-name

## One-line description
<!--
  A single sentence, 120 characters or fewer, written in third person,
  starting with an action verb. Seeds the skill's frontmatter description.
  Examples:
    - Generates a formatted .docx proposal from a markdown brief.
    - Validates a CSV export against the billing schema and reports mismatches.
  AVOID first person ("I'll...", "we do..."), editorial fluff ("this is really useful"),
  or sentences longer than 120 chars.
-->
Describes what this skill does in a single third-person sentence starting with an action verb.

## Trigger phrases
<!--
  Between 5 and 10 distinct, quoted, verbatim phrases a real user would
  type in chat to invoke this skill. Phrases MUST be literal user speech,
  not abstract descriptions.
  Good: "convert this markdown to a word doc"
  Bad:  "markdown conversion things"
-->
- "run my skill"
- "do the thing"
- "generate output"
- "turn this into the result"
- "process this input"

## Inputs
<!--
  Name every input by type (file path, URL, prompt argument, stdin) and
  format. For file inputs, name the exact extension(s). For URL inputs,
  name the host pattern. Be specific — "some data" will fail the validator.
-->
A path to a `.txt` file containing the text to process. Optional second argument: output filename (defaults to input stem plus `.out.txt`).

## Outputs
<!--
  State the exact output path under `~/Claude/<skill>/` AND the format.
  Every skill writes under `~/Claude/<skill>/` per BP-021. Never `~/Desktop/`.
  Include at least one concrete path.
-->
A `.txt` file at `~/Claude/your-skill-name/<input-stem>.out.txt`. On success, prints the absolute output path to stdout.

## Happy-path walkthrough
<!--
  Either 10-30 lines of imperative prose OR 5-15 numbered/bulleted steps.
  Rules:
    - Imperative voice only. "Read X. Parse Y. Write Z." NOT "X is read."
    - Name every decision point.
    - Name every tool by slash-command if one is invoked.
    - Passive voice anywhere in this section is a hard fail.
-->
1. Read the input file from the path argument. Fail fast with exit code 1 if the path does not exist.
2. Validate the input is a well-formed text file (non-empty, under 50MB). Fail fast with a specific error if validation fails.
3. Process the input according to the skill's transformation rules.
4. Ensure the output directory `~/Claude/your-skill-name/` exists. Create it if missing.
5. Write the processed output to `~/Claude/your-skill-name/<input-stem>.out.txt`.
6. Print the absolute output path to stdout. Do not auto-open the file.

## Success signals
<!--
  At least 2 concrete, observable signals checkable from the output alone
  (per BP-017: Observable). No subjective judgments ("works well", "looks good").
  Each signal must be machine- or eyeball-verifiable from the artifacts.
-->
- The output file exists at the expected path after the skill completes.
- `file <output-path>` reports the expected file type.

## Failure modes
<!--
  At least 2 named failure scenarios, each with a specific handling strategy:
  fail-fast, retry with backoff, prompt-user, or write `BLOCKER:` per BP-028.
  "Bad input" without a handling strategy will fail the validator.
-->
- **Input file missing or unreadable** → fail-fast with exit code 1 and an error message naming the missing path.
- **Output directory cannot be created** (permission denied) → fail-fast with the permission error and the target path.

## Existing skills to reuse
<!--
  Either a slash-prefixed list of ecosystem skills this will compose with,
  OR the literal word `None` if the skill is self-contained.
  Per BP-034, only name a sub-skill here if it ALREADY exists at
  `~/.claude/skills/<name>/`. Proposing new sub-skills for single-consumer
  logic is a BP-034 violation — use a local `references/<topic>.md` instead.
-->
None

<!--
  ==================================================================
  OPTIONAL SECTIONS BELOW THIS LINE
  Each raises classifier confidence but never fails the validator.
  Keep the ones that apply to your skill; delete the rest.
  ==================================================================
-->

## Edge cases
<!--
  Specific pathological inputs the skill must handle gracefully.
  Drives fixture design for the factory's QA phase.
-->
- Empty input file → fail fast with an "empty input" error.
- Input with only whitespace → treated as empty; fails fast.

## Anti-goals
<!--
  What the skill must NOT do. Prevents scope creep during sub-skill authoring.
-->
- Do NOT modify the input file under any circumstance.
- Do NOT auto-infer missing fields — fail fast instead.

## Delivery
<!--
  Optional. Controls Phase 9 (materialize) behavior — the per-client
  repo + symlink + GitHub-creation step. Single field:

    Remote repo: yes | no

  - `yes` (default if omitted): Phase 9 calls `gh repo create --private`
    after materializing locally + symlinking, and adds `adamkingai` as
    a collaborator. Use this for real client deliveries that should
    land on GitHub for collaboration.
  - `no`: Phase 9 stops at the local repo + symlink. No GitHub call.
    Use this for development iteration, smoke-test runs, internal-only
    POCs, or any spec that should never publish.

  Per plan v2 D6 (FLIPPED): `gh` is the default because the steady
  state is real client deliveries. The escape hatch is per-spec, not
  per-invocation, so the spec carries the canonical intent.
-->
Remote repo: yes
