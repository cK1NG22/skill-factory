---
name: sibling-refs-skill
description: Fixture for edge case 1 — references as sibling .md files at skill root rather than in references/. Mirrors the /pptx and /pdf pattern.
allowed-tools: []
---

# sibling-refs-skill

Transformation skill with references placed alongside SKILL.md instead of inside a `references/` subdirectory. This is a BP-008 edge case but is in active use by `/pptx` and `/pdf` in the wild.

## Procedure
Read the input. Apply the conversion using `editing.md` as the authoritative operations reference. Write the output.
