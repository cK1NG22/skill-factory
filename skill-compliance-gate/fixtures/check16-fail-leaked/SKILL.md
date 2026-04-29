---
name: acme-board-memo
description: Stage 13 Check 16 FAIL fixture. Simulates a delivered client skill that incorrectly carries the factory-internal meta-skill marker. The slug "acme-board-memo" is not in FACTORY_INTERNAL_SLUGS so Check 16 should fail. Use when testing Check 16's cross-scope leak detection. Trigger phrases included so check #7 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
meta-skill: true
---

# Stage 13 Check 16 — FAIL Fixture (Cross-Scope Leak)

This fixture simulates a client skill that mistakenly carries
`meta-skill: true` in its frontmatter. The slug `acme-board-memo` clearly
identifies a per-client deliverable, not one of the nine factory-internal
slugs. Check 16 should detect the cross-scope leak and emit a BLOCKER.

## Procedure

1. Do nothing. This fixture exists to demonstrate Check 16's cross-scope
   leak FAIL path.
