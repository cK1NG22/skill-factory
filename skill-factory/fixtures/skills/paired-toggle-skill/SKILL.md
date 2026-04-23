---
name: paired-toggle-skill
description: Fixture for edge case 4 — mentions /unfreeze as a companion command but does not invoke it via Agent. Mirrors /freeze.
allowed-tools:
  - Read
---

# paired-toggle-skill

Mode toggle that is the companion of `/unfreeze`. When the user invokes this skill, it writes a sentinel file to disk. When the user invokes `/unfreeze` (a separate command the user runs directly), the sentinel is removed.

## Procedure
Ask the user for the directory to freeze. Write the sentinel. Print a confirmation that lists the frozen path and reminds the user to run `/unfreeze` when done. This skill never spawns `/unfreeze` itself — that is a user-initiated companion action.
