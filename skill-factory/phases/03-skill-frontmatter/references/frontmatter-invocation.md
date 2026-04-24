# skill-frontmatter invocation contract (phase-scoped)

Phase-scoped reference for Phase 3. Cited by `../director.md`.

## The pack shape skill-frontmatter expects

`build_context_pack.py <spec> <classifier.json> skill-frontmatter <out-dir>`
materializes an `input.md` with these sections (matches the general
BP-033 contract at `../../references/invocation-contract.md`):

1. **`# Task`** — "Produce a compliant frontmatter YAML block for the
   skill described in the spec excerpt below."
2. **`## Spec excerpt`** — only the fields frontmatter needs: `Company`,
   `Skill slug`, `One-line description`, `Inputs`, `Outputs`, plus any
   walkthrough lines needed to infer `allowed-tools`.
3. **`## Classified traits`** — the 5 traits (mainly for `has_hitl` and
   `invokes_skills` context when composing the description).
4. **`## BPs to enforce`** — absolute paths to BP-001 (description
   contains trigger phrases), BP-002 (negative-case clause), BP-003
   (name format), BP-004 (description length ≤ 350 chars), BP-005
   (allowed-tools declared).
5. **`## Output locations`** — absolute paths for `output.yaml`,
   `output.md` (rationale), `notes.md` (blockers).

## What BP-set frontmatter adds on top of the base

Base universal BPs for this sub-skill (always applied):
- BP-001 — description contains trigger phrases
- BP-002 — description includes negative-case clause
- BP-003 — name format `<company>-<slug>`, combined ≤64 chars
- BP-004 — description length ≤ 350 chars
- BP-005 — allowed-tools declared

There are NO trait-gated additions for skill-frontmatter. It does not
register anything in `_SUB_SKILL_CONDITIONAL_BPS`. The base list is the
whole list.

## output.yaml shape the driver reads

```yaml
---
name: <company>-<slug>
description: <350-char description with trigger phrases and negative case>
allowed-tools: <comma-separated list>
argument-hint: <optional>
---
```

The lint script checks all 5 rules mechanically. The driver only reads
`passed`, `fails[]`, and `warns[]` from the lint's JSON output — it does
not re-parse the YAML itself.

## BLOCKER discipline

Per `../../references/spawn-subagent.md` and BP-028: the sub-skill
retries ONCE internally on a first lint failure. On the second failure,
the sub-skill writes `BLOCKER: <reason>` to `notes.md` and stops. The
driver reads the BLOCKER and halts the factory run.

Common BLOCKER causes:
- Combined name length > 64 chars (upstream spec bug — the author must
  shorten the Skill slug).
- Description length > 350 chars after trimming (upstream spec bug —
  the One-line description was too long to fit the template).
- Missing trigger phrase (upstream spec bug — One-line description
  didn't name the user-facing trigger).

## Why Phase 3 is non-conditional

Every skill has frontmatter. There is no trait, and no spec shape, under
which a skill would ship without it. This makes Phase 3 the only
always-firing sub-skill phase (Phase 1 is the validator Agent, which is
always-firing but a different kind of Agent).
