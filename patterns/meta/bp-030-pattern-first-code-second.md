# BP-030: Pattern first, code second; sub-skill catalog entry first, code second

**Source:** Stage cadence rules
**Category:** Authoring discipline (Meta — factory PR workflow)

**Why:** Documentation enables, not documents-after. A pattern that can't be articulated clearly enough for a dedicated `patterns/bp-NNN-*.md` file isn't a pattern — it's a vibe. A sub-skill without a `SKILLS.md` entry can't be reasoned about by collaborators.

**When applicable:** Every PR to `skill-factory`. Factory-internal PR discipline.

**Enforced by:** `CONTRIBUTING.md` workflow; CI compliance check (when added).

**Correct:** PR adds `patterns/bp-NNN-*.md` file + index row → second PR adds the sub-skill code that enforces it.

**Incorrect:** PR adds new sub-skill behavior without updating the patterns catalog or SKILLS.md.
