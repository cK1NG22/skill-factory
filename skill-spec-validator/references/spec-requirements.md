# Client Spec Requirements

**Authoritative contract every `client-spec.md` must satisfy.** `skill-spec-validator` reads this file and applies every rule to the input spec. Each section below is either **required** (hard-fails if missing or ambiguous) or **optional** (reported as present/absent but never fails).

---

## Required sections

Every client-spec.md MUST contain all 10 of these, in any order, each as its own markdown header (any level — `#`, `##`, or `###` is fine as long as the header text matches).

### 1. Company
- **Match pattern:** header containing the word `Company` (case-insensitive)
- **Content rule:** the first non-empty line after the header must contain a single lowercase-hyphenated slug, 2-32 chars, matching `^[a-z][a-z0-9-]*$`. This slug becomes `<company>` in `~/Projects/<company>-claude-skills/`.
- **Fix if missing:** "Add a '## Company' section with a lowercase-hyphenated slug (e.g., `acme`, `bravo-corp`). This becomes the folder name for the client's skill repo."
- **Fix if ambiguous:** "Company slug must be lowercase letters, digits, and hyphens only, 2-32 chars. Example: `acme`, not `Acme_Corp`."

### 2. Skill slug
- **Match pattern:** header containing the words `Skill slug` or `Slug` (case-insensitive)
- **Content rule:** lowercase-hyphenated slug, 2-40 chars, `^[a-z][a-z0-9-]*$`. Must NOT include the company prefix (factory prepends it).
- **Fix if missing:** "Add a '## Skill slug' section with a short hyphenated identifier for the skill itself (e.g., `onboarding-checklist`). Do NOT include the company prefix — the factory prepends it."
- **Fix if ambiguous:** "Skill slug must be lowercase letters, digits, and hyphens only, 2-40 chars. Strip any company prefix if present."

### 3. One-line description
- **Match pattern:** header containing `One-line description` or `Description` (case-insensitive)
- **Content rule:** a single line of prose, ≤ 120 characters, written in third person, starting with an action verb (e.g., "Generates X from Y", "Validates X against Y", "Converts X to Y"). Seeds the frontmatter description.
- **Fix if missing:** "Add a '## One-line description' section containing a single ≤120-char sentence in third person, action-verb-first. Example: 'Generates a formatted .docx from a markdown file.'"
- **Fix if ambiguous:** "Description is > 120 chars, uses second person, or doesn't start with an action verb. Rewrite as third-person imperative, ≤ 120 chars."

### 4. Trigger phrases
- **Match pattern:** header containing `Trigger` (case-insensitive)
- **Content rule:** 5 to 10 distinct phrases, each quoted and verbatim, that a user would naturally say to invoke this skill. Phrases may be bulleted or comma-separated.
- **Fix if missing:** "Add a '## Trigger phrases' section with 5-10 verbatim phrases users would say. Example: \"'convert markdown to docx', 'md to word doc', 'turn this md into word'\"."
- **Fix if ambiguous:** "Fewer than 5 phrases, or phrases are abstract descriptions rather than verbatim user speech. Include literal quotes a real user would type."

### 5. Inputs
- **Match pattern:** header containing `Inputs`
- **Content rule:** names each consumable by type (file path, URL, prompt arg, stdin) and format. For file inputs, names the file extension(s). Specificity required — "some data" is ambiguous.
- **Fix if missing:** "Add a '## Inputs' section describing what the skill consumes: file paths (with extensions), URLs, prompt arguments, stdin. Be specific about formats."
- **Fix if ambiguous:** "Inputs are described too vaguely. Name the exact file types, URL patterns, or prompt arg names. Example: 'A path to a .md file' not 'a markdown thing'."

### 6. Outputs
- **Match pattern:** header containing `Outputs`
- **Content rule:** states the exact output location (under `~/Claude/<skill>/` per BP-021) AND the output format (file extension, structured text, stdout message). Must include at least one concrete path.
- **Fix if missing:** "Add an '## Outputs' section specifying exact path (under ~/Claude/<skill>/) AND format. Example: 'A .docx file at ~/Claude/<skill>/<input-stem>.docx'."
- **Fix if ambiguous:** "Output location or format is unspecified. Name the exact path under ~/Claude/ AND the file type or message format. Never ~/Desktop/."

### 7. Happy-path walkthrough
- **Match pattern:** header containing `Happy-path` or `Walkthrough` or `Happy path`
- **Content rule:** EITHER 10-30 lines of prose OR 5-15 numbered/bulleted steps (your choice). In either form: every decision point named, every tool named by slash-command, uses imperative voice ("Read X. Validate Y. Write Z."), not passive ("X is read"). Passive voice anywhere in the walkthrough is a fail.
- **Fix if missing:** "Add a '## Happy-path walkthrough' section with 10-30 lines of imperative prose tracing input → output. Name every decision point and tool used."
- **Fix if ambiguous:** "Walkthrough uses passive voice, is fewer than 10 lines, or skips decision points. Rewrite as imperative steps: 'Read X. Parse Y. For each Z, do W. Write result to <path>.'"

### 8. Success signals
- **Match pattern:** header containing `Success` (case-insensitive)
- **Content rule:** at least 2 concrete, observable signals. Each must be checkable from the output alone (per BP-017: Observable). Examples: "file exists at <path>", "exit code 0", "compliance passes 13/13", "opens in Word", "contains at least 5 trigger phrases".
- **Fix if missing:** "Add a '## Success signals' section with 2+ concrete observables. Each must be checkable from output alone (no inference required)."
- **Fix if ambiguous:** "Signals are subjective ('looks good', 'works well') rather than observable. Replace with concrete checks: 'file exists at X', 'contains Y', 'returns Z'."

### 9. Failure modes
- **Match pattern:** header containing `Failure` or `Errors`
- **Content rule:** at least 2 named failure scenarios with desired handling (fail-fast, retry, prompt-user, write BLOCKER, etc.).
- **Fix if missing:** "Add a '## Failure modes' section listing at least 2 known failure scenarios and how the skill should handle each (fail-fast, retry, prompt, BLOCKER)."
- **Fix if ambiguous:** "Failure modes listed without handling guidance. For each scenario, specify what the skill should DO when it happens."

### 10. Existing skills to reuse
- **Match pattern:** header containing `Existing skills` or `Reuse`
- **Content rule:** either an explicit list of skills (each prefixed with `/`) OR the literal text `None` (if the skill is self-contained). An empty section fails.
- **Additional BP-034 check:** for each `/<skill>` named, confirm the skill exists at `~/.claude/skills/<skill>/` OR is a known ecosystem skill. Per BP-034, sub-skills are only justified when there's cross-skill reuse — if the named skill doesn't exist and the spec appears to propose creating it just for this one skill, that's a violation (should be a reference file, not a sub-skill).
- **Fix if missing:** "Add an '## Existing skills to reuse' section listing skills this will compose with (each as /<skill-name>), or the single word 'None' if self-contained."
- **Fix if ambiguous:** "Section is present but empty or lists skills without the / prefix. List as '/docx, /browse' or write 'None'."
- **Fix if BP-034 violation (named skill doesn't exist):** "The skill '/<name>' named here does not exist at ~/.claude/skills/<name>/. Per BP-034, sub-skills are only for cross-skill reuse — single-skill sub-processes stay as reference files. Either (a) create '/<name>' as a first-class ecosystem skill with its own reuse justification BEFORE building this one, or (b) remove it from this section and add the sub-process as a `references/<topic>.md` file inside this skill instead."

---

## Optional sections

These RAISE classification confidence but never cause failure. Report present-or-absent only.

### Edge cases
- **Match pattern:** header containing `Edge case` or `Edge cases`
- **Value added:** specific pathological inputs the skill must handle gracefully. Drives fixture design.

### Anti-goals
- **Match pattern:** header containing `Anti-goal` or `Anti-goals` or `Non-goal` or `Non-goals`
- **Value added:** what the skill explicitly should NOT do. Prevents scope creep in sub-skill outputs.

### Reference exemplars
- **Match pattern:** header containing `Reference exemplar` or `Exemplar` or `Like`
- **Value added:** names an existing skill the target skill should resemble (e.g., "like /411-deck but for ad copy").

### Scheduling
- **Match pattern:** header containing `Schedule` or `Scheduling` or `Cron`
- **Value added:** cron expression or description of invocation frequency. Required-ish for cron archetype (but validator only reports presence; archetype rubric enforces requirement).

### Hooks needed
- **Match pattern:** header containing `Hook` or `Hooks`
- **Value added:** PreToolUse hooks for mode-toggle and asymmetric-write-control archetypes.

---

## How the validator uses this file

- Required rules are applied in order. Validator returns `missing_required` entries for sections where the match_pattern doesn't hit, and `ambiguous_required` entries where it hits but the content_rule fails.
- Optional rules are applied AFTER required rules pass. They only populate `optional_present`.
- The `fix` strings in this file are literal — the validator returns them verbatim in its output. Writing better `fix` strings here = better user experience, no code changes needed.

## How to extend this contract

1. Draft the new rule (required or optional) as a PR to PATTERNS.md first, getting a `BP-###` entry.
2. Add the rule to this file following the format above.
3. Update the fixtures (`passing-spec.md` to satisfy the new rule, `gaps-spec.md` to demonstrate failing it).
4. Update `expected-pass.md` + `expected-gaps.md` to match.
5. Run the validator against the updated fixtures and verify diff is empty.

Rule additions here are NOT backward compatible — existing specs may suddenly fail. Coordinate with Carter before adding required rules.
