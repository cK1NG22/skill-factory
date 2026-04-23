# Spec Anti-Patterns

Common failure modes in `client-spec.md` files, with the fix for each. Read this before writing your first spec, and refer back when `/skill-spec-validator` returns a gap report.

This file is **documentation**, not a spec itself. The validator is not meant to be run on it; it is meant to be read by spec authors before running the validator on their own specs.

Each anti-pattern below is structured:
- **Bad** — a snippet that fails the validator or produces a broken skill downstream.
- **Why it fails** — which content rule (or downstream assumption) this violates.
- **Fix** — a rewritten snippet that passes.

The authoritative contract is `skill-spec-validator/references/spec-requirements.md`. When this file and the contract drift, trust the contract.

---

## 1. Vague outputs

### Bad
```md
## Outputs
An onboarding checklist.
```

### Why it fails
Rule 6 (Outputs) requires an exact path under `~/Claude/<skill>/` AND a format. "An onboarding checklist" names neither. Downstream sub-skills cannot choose a writer (docx? markdown? stdout?), cannot choose a path, and cannot infer a filename convention. Every one of those missing details becomes a guess, and the factory's quality ceiling is pinned to the worst guess.

### Fix
```md
## Outputs
A `.docx` file at `~/Claude/acme-onboarding/<new-hire-id>-checklist.docx`. On success, prints the full output path to stdout so the caller can open it immediately.
```

---

## 2. Missing failure handling

### Bad
```md
## Failure modes
- Bad input.
- Network errors.
```

### Why it fails
Rule 9 (Failure modes) requires each scenario paired with a handling strategy: fail-fast, retry-with-backoff, prompt-user, or write `BLOCKER:` per BP-028. "Bad input" names the scenario but leaves the skill to invent its own policy. In practice this becomes silent swallowing of errors — the single most expensive bug class in the ecosystem, because it produces outputs that LOOK successful until a human inspects them.

### Fix
```md
## Failure modes
- **Input file missing or unreadable** → fail-fast with exit code 1 and an error message naming the missing path.
- **Input file is malformed YAML (schema validation fails)** → fail-fast with a specific error naming the first offending field and line number.
- **Network error when calling the HRIS API** → retry up to 3 times with exponential backoff (1s, 2s, 4s). If all retries fail, write `BLOCKER: HRIS API unreachable after 3 retries` to `notes.md` per BP-028 and exit cleanly.
- **Output directory cannot be created** (permission denied) → fail-fast with the permission error and the target path.
```

---

## 3. Conflicting or non-verbatim trigger phrases

### Bad
```md
## Trigger phrases
- Onboarding things
- When new people join the company
- HR workflow automation
```

### Why it fails
Rule 4 (Trigger phrases) requires 5-10 distinct, quoted, verbatim phrases a real user would type. The bad version is a set of descriptions, not quotations. No user types "onboarding things" in chat; they type "onboard this new hire" or "set up the new guy from Monday". Descriptions produce a classifier that never triggers on real speech — the skill ships and is never used.

Also: fewer than 5 phrases fails the quantity rule, even if the phrases are verbatim.

### Fix
```md
## Trigger phrases
- "onboard this new hire"
- "set up the new hire"
- "new employee onboarding"
- "generate onboarding checklist"
- "first day setup for <name>"
- "run onboarding for the new person"
```

Write them the way a real user actually types. Include typos, abbreviations, and colloquialisms if they are real — the classifier benefits from seeing them.

---

## 4. Single-use sub-skill proposals (BP-034 violation)

### Bad
```md
## Existing skills to reuse
- /acme-generate-checklist — generates the 14-item checklist
- /acme-send-welcome-email — sends the welcome email
- /acme-log-sent-mail — logs sent mail to the audit trail
```

(None of `/acme-generate-checklist`, `/acme-send-welcome-email`, or `/acme-log-sent-mail` exist in the ecosystem. The author is proposing three new sub-skills that will be invoked only by this one parent skill.)

### Why it fails
BP-034: sub-skills are justified only by **cross-skill reuse**. A sub-process consumed by exactly one skill is an accidental indirection. Every Agent-spawn boundary costs a context copy and a serialization round-trip. Two spawn boundaries for a 30-line transformation is pure overhead.

The validator also runs a filesystem check: any `/<skill>` named here must exist at `~/.claude/skills/<skill>/`. Naming a skill that does not exist is almost always a sign the author meant to propose a reference file, not a sub-skill.

### Fix
Either **(a)** move the logic into this skill as a local `references/<topic>.md` file (for prose-style logic) or a local script (for deterministic logic), **OR (b)** if the logic really will be shared across two or more ecosystem skills, create the sub-skill as a first-class citizen with its own `client-spec.md` FIRST, get it through the factory, and then reference it here after it exists.

```md
## Existing skills to reuse
- `/send-email` — existing ecosystem skill for sending email; reused here for the welcome message.
- Checklist rendering: local `references/checklist-template.md` (single-consumer, not a sub-skill).
- Audit logging: local `references/audit-format.md` (single-consumer, not a sub-skill).
```

---

## 5. Passive voice in the walkthrough

### Bad
```md
## Happy-path walkthrough
The new hire's information is collected. The checklist is generated from the template. Emails are sent to the hire and their manager. The process is tracked over the first week.
```

### Why it fails
Rule 7 (Happy-path walkthrough) is explicit: passive voice anywhere in this section is a hard fail. Passive voice hides the agent — "collected by whom? generated by what? sent by which tool?" — and the classifier depends on subject-verb-object clarity to distinguish trigger conditions from executor actions.

This is also a shorter-than-minimum walkthrough (4 lines of prose, below the 10-line floor).

### Fix
```md
## Happy-path walkthrough
1. Read the new-hire record from `~/Claude/acme-onboarding/hires/<id>.yaml`. Fail fast if the file is missing or the YAML is malformed.
2. Validate the record against the HRIS schema. Fail fast with a specific field name if validation fails.
3. Render the 14-item checklist using the template at `references/checklist-template.md`. Substitute the hire's name, manager, start date, and role into each item.
4. Invoke `/docx` to write the checklist to `~/Claude/acme-onboarding/<id>-checklist.docx`.
5. Invoke `/send-email` with the checklist attached, addressed to the hire and their manager.
6. Append an entry to `~/Claude/acme-onboarding/sent.log` recording the timestamp, hire id, and recipients.
7. Print the output path of the checklist to stdout. Do not auto-open.
```

---

## 6. Subjective success signals

### Bad
```md
## Success signals
- The skill works well.
- New hires are happy.
- HR saves time.
```

### Why it fails
Rule 8 (Success signals) requires each signal to be checkable **from the output alone** (per BP-017: Observable). "Works well" is a judgment call. "New hires are happy" requires a survey weeks later. "HR saves time" needs longitudinal data across many runs. None of these can be verified by inspecting the skill's output artifact immediately after a run, which is what the factory's QA phase needs.

### Fix
```md
## Success signals
- The output `.docx` file exists at the expected path after the skill completes.
- The output contains exactly 14 checklist items, matching the template.
- Every checklist item has a Word form-control checkbox (not plain text).
- `~/Claude/acme-onboarding/sent.log` has a new line for this run with the correct hire id and timestamp.
- The `/send-email` log records a successful send to both the hire and their manager.
```

---

## 7. Description too long or in the wrong voice

### Bad
```md
## One-line description
This skill is going to be really useful for the team because it'll guide new hires through their first day tasks and make sure they have everything they need and nothing is forgotten about in the process of joining the company, plus it'll save HR a lot of time because they don't have to manually check in with every new person anymore.
```

### Why it fails
Rule 3 (One-line description) requires ≤120 characters, third person, starting with an action verb. The bad version is 352 chars, first person (`it'll`, implicit `we`), and opens with editorial framing ("this skill is going to be") rather than a function verb. The frontmatter description is seeded from this line — a bloated description becomes the skill's public tagline forever.

### Fix
```md
## One-line description
Generates a first-day onboarding checklist from a new-hire record and emails it to the hire and their manager.
```

107 chars. Third person. Starts with `Generates`. States the function.

---

## 8. Archetype hint (retired — do not include)

### Bad
```md
## Archetype hint
phased-HITL
```

### Why it fails
As of ADR-0001 (2026-04-23), the fixed 15-archetype taxonomy was retired in favor of a rule engine over 5 traits (`has_references`, `has_phases`, `has_hitl`, `is_scheduled`, `invokes_skills`). The `## Archetype hint` section was removed from the validator contract entirely. The factory derives traits automatically from the other required sections; it does not read any archetype hint. Including the section produces noise at best, and at worst causes a spec author to think the hint will steer classification when it will not.

### Fix
Omit the `## Archetype hint` section entirely. Do not include it in new specs. If you are editing an older spec that still has one, delete the section — it will not be read.

---

## 9. Template form-fill mistakes (semantic, not syntactic)

These pass the validator because they satisfy every content rule syntactically. They still produce broken skills, because the validator cannot detect the author's intent.

- **Leaving `your-company` as the literal Company slug.** Creates a repo at `~/Projects/your-company-claude-skills/`. Valid regex; obviously wrong. Sanity-check every placeholder before running `/skill-factory`.
- **Leaving the template's stub walkthrough steps ("process the input according to the skill's transformation rules") unmodified.** The validator sees 6 imperative numbered steps and passes. The authored skill ships with generic "transform each element" logic that does nothing useful.
- **Listing `None` under "Existing skills to reuse" when your walkthrough actually invokes `/docx` or `/send-email`.** Validator passes (the section is present and non-empty). The driver's trait classifier sets `invokes_skills: false` incorrectly, producing a skill whose compliance check later flags the inconsistency.

The fix for each is the same: read your finished spec end-to-end before running the validator, and make sure every section is a statement about *this* skill, not about the template.

---

## What to do if you believe the validator is wrong

If a validator failure feels like a false positive (the rule seems too strict for your legitimate case):

1. Do NOT work around it by padding content to pass.
2. File an issue against `skill-spec-validator/references/spec-requirements.md` citing the specific rule and your case.
3. If the rule is amended, re-run the validator. If not, fix the spec.

The validator is the factory's only human gate (per BP-026). Weakening it via spec gymnastics silently undermines every downstream sub-skill. Strictness here is cheaper than rework five phases later.
