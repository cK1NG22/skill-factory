---
name: skill-frontmatter
description: Stage 13 Check 15 FAIL fixture exercising Signal 1. The slug is in BP033_PHASE_SUBSKILL_SLUGS so Check 15 fires; the canonical BP-033 opening sentence is intentionally absent. Use when testing the gate's preamble-missing failure mode. Trigger phrases present so check #7 passes; description is over 100 chars so check #8 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
meta-skill: true
---

# Stage 13 Check 15 — FAIL Fixture (Signal 1)

This sub-skill body deliberately omits the canonical BP-033 opening
sentence. A real phase sub-skill must begin by directing itself to its
own driver-materialized pack file under the `phases/` tree. Without that
sentence, Signal 1 of Check 15 fires.

## Procedure

1. Do nothing. This fixture exists to exercise the gate's
   preamble-missing FAIL path.
