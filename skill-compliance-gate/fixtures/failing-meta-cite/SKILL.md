---
name: skill-compliance
description: Fixture that cleanly passes the 13 compliance checks but violates Check 14 by citing a meta-BP inside references/. Used by skill-compliance-gate tests. Trigger phrases present; description is longer than 100 chars so check #8 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
---

# Fixture Failing Meta Cite

This fixture is structurally valid per the 13-check audit. The BP violation
lives inside `references/` so it surfaces only on Check 14 (scan meta-BP
citations). The gate should FAIL on this fixture.
