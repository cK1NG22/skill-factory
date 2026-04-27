---
name: fixture-failing-required
description:
allowed-tools:
  - Read
---

# Fixture Failing Required

This fixture deliberately has an empty `description` field in its
frontmatter. `compliance_check.py` check #4 (`description_exists`,
severity `required`) will flag this with `status: fail`. The gate's
Rule 1 (any required-tier FAIL → BLOCKER) should fire on this fixture.

Used by `skill-compliance-gate/tests/test_gate.py` to verify the
required-failure path of the gate.
