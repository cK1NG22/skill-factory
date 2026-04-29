---
name: skill-frontmatter
description: Stage 13 Check 15 PASS fixture. Slug is in BP033_PHASE_SUBSKILL_SLUGS so Check 15 fires; the BP-033 preamble is present and no concrete patterns/bp-NNN-name.md path appears in the sub-skill tree. Use when testing the Check 15 happy path. Trigger phrases included so check #7 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
meta-skill: true
---

# Stage 13 Check 15 — PASS Fixture

**Read ONLY your `phases/01-skill-frontmatter/input.md`** (per BP-033). The
driver materializes BP citations into the input pack — do not reach into
the patterns corpus directly.

## Procedure

1. Do nothing. This is a fixture, not a real skill.

## Why this fixture exists

Stage 13 Check 15 inspects driver-launched phase sub-skills for two
signals: a "Read ONLY ... input.md" preamble and the absence of any
concrete `patterns/bp-NNN-name.md` direct read in the sub-skill tree. This
fixture demonstrates both signals satisfied — slug is in the phase
sub-skill set, the preamble is present, and the body uses only the
template form `patterns/bp-NNN-*.md` (literal "NNN" letters) when
describing the input contract, which Check 15 does not match.
