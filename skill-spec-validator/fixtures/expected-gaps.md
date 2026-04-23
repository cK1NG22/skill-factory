# Expected output — gaps-spec.md

When `skill-spec-validator` runs against `fixtures/gaps-spec.md`, it should produce the following.

## Expected failures

The gaps fixture is designed to fail in specific, enumerable ways:

| # | Section | Failure mode | Why |
|---|---|---|---|
| 1 | Company | ambiguous | Value `Acme_Corp` contains uppercase + underscore — violates `^[a-z][a-z0-9-]*$` |
| 2 | One-line description | ambiguous | Far exceeds 120-char limit (≈ 340 chars) |
| 3 | Trigger phrases | missing | No `## Trigger phrases` header anywhere in the spec |
| 4 | Inputs | ambiguous | "Some data" is too vague; no file type or format named |
| 5 | Outputs | ambiguous | No path under `~/Claude/` specified; no file format given |
| 6 | Happy-path walkthrough | ambiguous | Passive voice throughout; fewer than 10 lines; decision points unnamed |
| 7 | Success signals | ambiguous | Subjective claims ("works well", "happy", "saves time") rather than observable |
| 8 | Failure modes | ambiguous | Scenarios named but no handling specified |
| 9 | Existing skills to reuse | missing | No header present at all |

Total: **2 missing_required, 7 ambiguous_required, 0 optional sections present.**

## output.yaml (authoritative — diff against this)

```yaml
status: gaps
spec_path: /Users/carterking/Projects/skill-factory/skill-spec-validator/fixtures/gaps-spec.md
missing_required:
  - section: "Trigger phrases"
    line: null
    fix: "Add a '## Trigger phrases' section with 5-10 verbatim phrases users would say. Example: \"'convert markdown to docx', 'md to word doc', 'turn this md into word'\"."
  - section: "Existing skills to reuse"
    line: null
    fix: "Add an '## Existing skills to reuse' section listing skills this will compose with (each as /<skill-name>), or the single word 'None' if self-contained."
ambiguous_required:
  - section: "Company"
    line: 4
    issue: "Value 'Acme_Corp' contains uppercase letters and an underscore."
    fix: "Company slug must be lowercase letters, digits, and hyphens only, 2-32 chars. Example: `acme`, not `Acme_Corp`."
  - section: "One-line description"
    line: 10
    issue: "Description exceeds 120 character limit (approximately 340 chars) and uses second person framing."
    fix: "Description is > 120 chars, uses second person, or doesn't start with an action verb. Rewrite as third-person imperative, ≤ 120 chars."
  - section: "Inputs"
    line: 13
    issue: "Content 'Some data about the new hire' does not name a file type, URL pattern, or specific argument."
    fix: "Inputs are described too vaguely. Name the exact file types, URL patterns, or prompt arg names. Example: 'A path to a .md file' not 'a markdown thing'."
  - section: "Outputs"
    line: 16
    issue: "Output location unspecified; format ('checklist') is abstract rather than a concrete file type or stdout format."
    fix: "Output location or format is unspecified. Name the exact path under ~/Claude/ AND the file type or message format. Never ~/Desktop/."
  - section: "Happy-path walkthrough"
    line: 19
    issue: "Walkthrough uses passive voice throughout ('is invoked', 'is collected', 'is generated'), is fewer than 10 lines, and does not name decision points or tools used."
    fix: "Walkthrough uses passive voice, is fewer than 10 lines, or skips decision points. Rewrite as imperative steps: 'Read X. Parse Y. For each Z, do W. Write result to <path>.'"
  - section: "Success signals"
    line: 22
    issue: "Signals are subjective ('works well', 'happy', 'saves time') rather than observable from output alone."
    fix: "Signals are subjective ('looks good', 'works well') rather than observable. Replace with concrete checks: 'file exists at X', 'contains Y', 'returns Z'."
  - section: "Failure modes"
    line: 27
    issue: "Scenarios named ('Bad input', 'Network errors') but no handling strategy specified for either."
    fix: "Failure modes listed without handling guidance. For each scenario, specify what the skill should DO when it happens."
optional_present: []
ready_for_classify: false
```

## output.md (human-readable version — wording may vary slightly, content must match)

```markdown
# Spec validation report — gaps-spec.md

**STATUS: gaps** ❌

The spec has 2 missing required sections and 7 ambiguous required sections. Fix each item below, then re-run the validator.

## Missing required sections (2)
1. **Trigger phrases** — Add a '## Trigger phrases' section with 5-10 verbatim phrases...
2. **Existing skills to reuse** — Add an '## Existing skills to reuse' section listing skills...

## Ambiguous required sections (7)
1. **Company** (line 4) — Value 'Acme_Corp' contains uppercase letters and an underscore. Fix: ...
2. **One-line description** (line 10) — Description exceeds 120 character limit... Fix: ...
3. **Inputs** (line 13) — Content 'Some data about the new hire' does not name a file type... Fix: ...
4. **Outputs** (line 16) — Output location unspecified... Fix: ...
5. **Happy-path walkthrough** (line 19) — Walkthrough uses passive voice throughout... Fix: ...
6. **Success signals** (line 22) — Signals are subjective... Fix: ...
7. **Failure modes** (line 27) — Scenarios named but no handling strategy specified... Fix: ...

## Optional sections present (0)
_None._

## Next step
Address the 9 issues above in the spec file, then re-run `/skill-spec-validator` against the updated path.
```

## Acceptance criteria

- `status` is exactly the string `gaps`.
- `missing_required` has exactly 2 entries (Trigger phrases, Existing skills to reuse).
- `ambiguous_required` has exactly 7 entries covering the sections enumerated above.
- Every `fix` string matches the literal `fix_if_missing` or `fix_if_ambiguous` value from `references/spec-requirements.md` (validator returns them verbatim).
- Each `ambiguous_required` entry has a `line` number and an `issue` field that names the specific problem.
- `ready_for_classify` is literally the boolean `false`.
- `optional_present` is the empty list `[]`.

## Notes on line numbers

Line numbers refer to the position in `gaps-spec.md` where the problematic content starts (not the header line itself). If the validator reports off-by-one consistently, update the expected values here after verifying the validator's convention is correct.
