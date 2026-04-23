# BP-021: Outputs go to `~/Claude/<skill>/`, never `~/Desktop/` or project dirs

**Source:** `feedback-output-home-convention.md`
**Category:** Output & rendering (Universal)

**Why:** `~/Desktop/` clutter is invisible-by-decay; project dirs pollute git status. `~/Claude/` is the single conventional output home with 30-day auto-archive.

**When applicable:** Every skill that writes files (Universal). Skills that only toggle state (e.g., `/freeze`) are a trivial no-op for this BP.

**Enforced by:** `skill-output-contract`, `skill-compliance`

**Correct:** Output saved to `~/Claude/skill-factory/<session>/draft-skill/`.

**Incorrect:** Output saved to `~/Desktop/output.docx` or `./generated-stuff/`.
