---
name: skill-factory
description: Stage 13 Check 15 SKIP fixture. Slug is "skill-factory" (the driver) which is in FACTORY_INTERNAL_SLUGS but NOT in BP033_PHASE_SUBSKILL_SLUGS. Check 15 should not fire because the driver does not consume a materialized input.md pack. Use when testing Check 15's allowlist gating. Trigger phrases included so check #7 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
meta-skill: true
---

# Stage 13 Check 15 — SKIP Fixture (Driver)

This fixture's slug is `skill-factory` — the driver itself. The driver
materializes input.md packs FOR sub-skills; it does not read them. Check
15 must skip this skill because the BP-033 preamble requirement and the
no-direct-`patterns/`-read constraint apply only to sub-skills that
consume packs.

This fixture intentionally omits the BP-033 preamble and includes no
`patterns/bp-NNN-name.md` references — Check 15 should report
`{checked: false}` regardless.

## Procedure

1. Do nothing. This fixture exists to demonstrate Check 15's
   non-sub-skill skip path.
