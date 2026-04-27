---
name: skill-factory-meta-fixture
description: Factory-internal meta-skill fixture used by Phase 9 tests to verify the meta-skill skip path. Use when "test meta-skill skip" or "phase 9 short-circuit". Do NOT install — this is a test fixture only.
allowed-tools:
  - Read
meta-skill: true
---

# skill-factory-meta-fixture

A factory-internal meta-skill fixture. Phase 9 must short-circuit on this
because of the `meta-skill: true` frontmatter marker.

## Happy-path walkthrough

1. Materializer reads frontmatter.
2. Materializer detects meta-skill marker.
3. Materializer returns skipped="meta" without touching the filesystem.
