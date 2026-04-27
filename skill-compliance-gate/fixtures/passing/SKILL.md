---
name: fixture-passing-skill
description: Minimal fixture skill used by skill-compliance-gate's tests to verify the clean-PASS path. Use when testing the gate's happy path. Trigger phrases are present so check #7 passes; description is longer than 100 chars so check #8 passes.
argument-hint: "<no-args>"
allowed-tools:
  - Read
---

# Fixture Passing Skill

A minimal, clean skill that should pass every one of the 13 compliance
checks plus Check 14. It exists solely as a test fixture for
`skill-compliance-gate/tests/test_gate.py`.

## Procedure

1. Do nothing. This is a fixture, not a real skill.

## Why this fixture is intentionally small

The gate's clean-PASS path needs one byte-stable input. Making the fixture
as small as possible minimizes the test's fragility: a later addition to
`compliance_check.py` that introduces a new best-practice WARN does not
affect this fixture because the body is under 200 lines and the
best-practice WARNs are non-blocking for the gate anyway.
