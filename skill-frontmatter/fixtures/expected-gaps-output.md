# Expected output — gaps-input.md

When `skill-frontmatter` runs against `fixtures/gaps-input.md`, it should fail at Step 4 (name construction) and emit a BLOCKER. This fixture proves the strict-stop discipline per BP-028.

## What's wrong with the gaps fixture

| Spec field | Value | Problem |
|---|---|---|
| Company | `verylongcompanyname-ltd-international` | 37 chars |
| Skill slug | `customer-onboarding-pipeline-with-all-the-features-included-and-more-comprehensive` | 82 chars |
| Combined `name` | would be `verylongcompanyname-ltd-international-customer-onboarding-pipeline-...` | 120 chars — exceeds the 64-char BP-003 limit |
| Trigger phrases | only 2 ("onboard", "run onboarding") | Below Rule 3's minimum of 3 AND the spec-validator's minimum of 5 |
| One-line description | "Onboards customers." | 19 chars — far below Rule 2's 80-char minimum |

## Expected behavior

The sub-skill should fail fast at Step 4 with a BLOCKER:

### notes.md

```
BLOCKER: combined name 'verylongcompanyname-ltd-international-customer-onboarding-pipeline-with-all-the-features-included-and-more-comprehensive' exceeds 64 char limit (len=121); upstream spec must shorten Skill slug.
```

The exact length in the BLOCKER line may differ by a character depending on whether the agent counts the joining hyphen; acceptance is "BLOCKER line present AND names the 64-char limit AND suggests upstream spec fix".

### output.yaml

**NOT produced.** The file should not exist after a gaps run.

### output.md

**NOT produced** (or produced empty / with only the BLOCKER restatement). Acceptance is "if output.md is produced, it does NOT contain a valid frontmatter block".

## Why this fixture matters

The gaps fixture proves three discipline rules at once:
1. **BP-028 BLOCKER convention** — the skill writes `BLOCKER:` rather than inventing a truncated name.
2. **Spec-is-authoritative** — the sub-skill does not silently "fix" an upstream spec problem; it surfaces it for the human to fix.
3. **Early-exit on impossible input** — the skill stops at Step 4 rather than proceeding through a degraded path that would produce a nonsense frontmatter.

## Acceptance criteria summary

1. `notes.md` exists and contains exactly one `BLOCKER:` line naming the 64-char limit.
2. `output.yaml` does NOT exist (or exists and is empty).
3. `output.md` either does not exist OR exists without a valid frontmatter block.
