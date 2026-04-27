---
name: acme-conflict-skill
description: Fixture used by the conflict-detection test. The factory will copy this then a test will mutate the copy to verify the BLOCKER fires on re-materialize. Use when "test materializer conflict" or "BP-028 conflict path". Do NOT use for real work.
allowed-tools:
  - Read
---

# acme-conflict-skill

This fixture exists solely to drive the BLOCKER-on-conflicting-skill-dir
test. It will be copied once, then a test will edit the copy on disk to
diverge from the fixture, then call materialize() a second time to verify
the BLOCKER fires.

## Happy-path walkthrough

1. First materialize: copies the fixture verbatim.
2. Test mutates the on-disk copy.
3. Second materialize: detects the divergence and BLOCKERs.
