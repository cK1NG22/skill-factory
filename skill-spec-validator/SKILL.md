---
name: skill-spec-validator
description: Validate a client-spec.md against the Skill Factory's input quality contract before the factory authors a skill from it. Either green-lights the spec or returns a surgical gap-report with specific fix instructions for each missing or ambiguous section. Use when "validate spec", "check the client spec", "spec check", "gate my spec", "will this spec work", "is my spec complete", "spec-validator", or any time a client-spec.md is about to be fed to /skill-factory. Do NOT use for generic document review — this checks ONE specific contract (the skill-factory spec schema).
argument-hint: "<path-to-client-spec.md>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# skill-spec-validator

The Skill Factory's input gate. Every `client-spec.md` must pass this validator before `/skill-factory` will author a skill from it. The validator is the **single human touchpoint** in the hands-off vision (per BP-026) — if the spec is complete and unambiguous here, the downstream pipeline runs without supervision. If not, you get a specific gap-report telling you exactly what to fix.

**What this skill does NOT do:** generic document review, stylistic edits, content critique. It checks ONE contract: the schema defined in `references/spec-requirements.md`. If a section is missing or ambiguous per those rules, the validator flags it. Nothing else.

## Invocation modes

### Standalone (human-invoked)
```
/skill-spec-validator ~/Claude/specs/acme-onboarding-spec.md
```
Reads the spec, applies the contract, prints `STATUS: pass` or `STATUS: gaps` with fix instructions to the terminal.

### Driver-invoked (called from /skill-factory Phase 1)
Called as an isolated `Agent` subtask from the Skill Factory driver. Reads from and writes to the driver's session workspace:

**Reads:**
- `phases/01-skill-spec-validator/input.md` — path to the spec being validated
- `spec.md` (the actual client-spec.md in the workspace root)

**Writes (to `phases/01-skill-spec-validator/`):**
- `output.md` — human-readable pass-or-gaps report
- `output.yaml` — machine-parseable status + details (driver reads this)
- `notes.md` — any `BLOCKER:` conditions (per BP-028) or observations

## Validation procedure

Follow these steps in order. Do NOT skip ahead or re-order. Every step has a reason — see `references/spec-requirements.md` for the why of each rule.

### Step 1 — Load the contract
Read `references/spec-requirements.md`. This file is authoritative. Every required section listed there MUST be checked against the input spec. Every optional section should be reported as present-or-absent (not failure).

### Step 2 — Read the input spec
Read the spec file referenced by the argument (standalone mode) or pointed at by `phases/01-skill-spec-validator/input.md` (driver mode).

### Step 3 — Check each required section
For each section in `references/spec-requirements.md`'s **Required** list, in order:

1. **Presence check.** Does a markdown header matching the section's `match_pattern` exist anywhere in the spec? If not, add to `missing_required` with:
   - `section`: the section name
   - `line`: `null`
   - `fix`: the rule's `fix_if_missing` string, **verbatim** from the contract file.

2. **Content check.** If the header exists, does the content immediately following it satisfy the rule's `content_rule`? If not, add to `ambiguous_required` with:
   - `section`: the section name
   - `line`: the line number in the spec of the **offending content** (not the header line) — this is the line the user needs to edit.
   - `issue`: a concrete description of what's specifically wrong in this spec (e.g., "line 12 uses passive voice; can't tell what triggers vs. what executes"). **Write this yourself.** This describes THIS failure in THIS spec.
   - `fix`: the rule's `fix_if_ambiguous` string, **verbatim** from the contract file. **Do not paraphrase.** This is the generic fix that works for any spec failing this rule; the user combines it with the `issue` to understand what to do.

**In short:** `issue` = concrete/custom, `fix` = verbatim/generic. Both required on every `ambiguous_required` entry.

### Step 4 — Check optional sections
For each section in the **Optional** list, just record whether it's present. Optional sections never fail — they only raise classification confidence downstream.

### Step 5 — Determine final status
- If `missing_required` AND `ambiguous_required` are both empty → `STATUS: pass`, `ready_for_classify: true`.
- Otherwise → `STATUS: gaps`, `ready_for_classify: false`.

### Step 6 — Write output
Produce `output.yaml` per the schema below. Write `output.md` as a human-readable version of the same content. If any step encountered an unexpected situation the validator cannot resolve (e.g., spec file missing, contract file missing), write `BLOCKER: <description>` as the first line of `notes.md` per BP-028.

## Output schema (authoritative)

### On pass
```yaml
status: pass
spec_path: /absolute/path/to/spec.md
sections_found:
  - Company
  - Skill slug
  - One-line description
  - Trigger phrases
  - Inputs
  - Outputs
  - Happy-path walkthrough
  - Success signals
  - Failure modes
  - Existing skills to reuse
optional_present:
  - Archetype hint
  - Edge cases
  - Anti-goals
ready_for_classify: true
```

`optional_present` lists every optional section whose `match_pattern` hit. Order matches the order of optional sections in `references/spec-requirements.md` for determinism. If zero optional sections were found, emit `optional_present: []`.

### On gaps
```yaml
status: gaps
spec_path: /absolute/path/to/spec.md
missing_required:
  - section: "Trigger phrases"
    line: null
    fix: "Add a '## Trigger phrases' section with 5-10 verbatim phrases users would naturally say. Example: \"'convert markdown to docx', 'md to word doc', 'turn this md into word'\"."
ambiguous_required:
  - section: "Outputs"
    line: 18
    issue: "Output location is unspecified. Only format is given."
    fix: "Specify exact output path under ~/Claude/<skill>/ and the file type. Example: 'A .docx file at ~/Claude/<skill>/<input-stem>.docx'."
optional_present:
  - Archetype hint
ready_for_classify: false
```

## Self-test against fixtures

The skill ships with two fixtures you can run against to verify it still works:

**Passing fixture:**
```
/skill-spec-validator ~/Projects/skill-factory/skill-spec-validator/fixtures/passing-spec.md
```
Expected: `STATUS: pass` + matches `fixtures/expected-pass.md`.

**Gaps fixture:**
```
/skill-spec-validator ~/Projects/skill-factory/skill-spec-validator/fixtures/gaps-spec.md
```
Expected: `STATUS: gaps` + matches `fixtures/expected-gaps.md`.

Diff the actual output against the expected file. Any drift means either the spec contract changed (update expected files) or the validator logic regressed (fix the skill).

## Patterns enforced (PATTERNS.md)

- **BP-026** — sole human touchpoint = the input spec
- **BP-027** — input gate before classify
- **BP-028** — BLOCKER convention for unresolvable ambiguity

## What to do if you're stuck

- **Spec file missing** → write `BLOCKER: spec file not found at <path>` to `notes.md`. Do not guess.
- **Contract file missing** → write `BLOCKER: references/spec-requirements.md not readable` to `notes.md`. Do not proceed.
- **Spec has structural anomalies** (non-markdown, binary, 10MB+) → write `BLOCKER: spec file is not a well-formed markdown document` to `notes.md`.
- **Ambiguity between "section missing" vs "section present but empty"** → treat "present but empty" as `ambiguous_required`, not `missing_required`. An empty section is a stronger signal of intent than a missing one.
- **Multiple issues in one section** → list them all in the same entry's `issue` field, joined by "; ".

## Why this skill is so strict

The factory's entire quality ceiling is set by the input spec. Every ambiguity here becomes a wrong sub-skill output downstream. Strictness at the gate is cheaper than rework at the compliance check five stages later. If this validator feels annoying, that's the feature.
