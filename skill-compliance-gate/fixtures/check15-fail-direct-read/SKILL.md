---
name: skill-frontmatter
description: Stage 13 Check 15 FAIL fixture (Signal 2 violation). Slug is in BP033_PHASE_SUBSKILL_SLUGS so Check 15 fires; preamble is present, but a referenced file cites a concrete patterns/bp-NNN-name.md path directly. Use when testing Check 15's direct-read failure mode. Trigger phrases included so check #7 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
meta-skill: true
---

# Stage 13 Check 15 — FAIL Fixture (Direct Read)

**Read ONLY your `phases/01-skill-frontmatter/input.md`** (per BP-033).

The preamble above is present and correct. The Check 15 violation lives
in `references/leaky.md`, which cites a concrete `patterns/bp-NNN-name.md`
path directly — the kind of read BP-033 forbids in sub-skills.

## Procedure

1. Do nothing. This fixture exists to demonstrate Check 15's direct-read
   FAIL path.
