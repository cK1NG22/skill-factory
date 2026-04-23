# Trait classifier edge cases

Four implementation gotchas in `scripts/trait_predicates.py` that the naive regex approach gets wrong. Each one is exercised by a fixture in `fixtures/skills/` and covered by a test in `tests/test_trait_predicates.py`. Surfaced by the 2026-04-23 matrix exercise against 20 ecosystem skills (see ADR-0001, §Evidence).

**Matrix noise without these fixes:** raw classifier misclassified ~30% of the 20-skill sample. Specifically, 12/20 flagged `invokes_skills=Y` on the raw scan; true rate after corrections is ~5/20.

---

## Edge case 1 — Sibling `.md` files count as `has_references`

**Who:** `/pptx` has `editing.md` + `pptxgenjs.md` at skill root. `/pdf` has `forms.md` + `reference.md`. Neither uses the `references/` subdirectory convention.

**The naive mistake:** only look inside `references/`. Skills that put reference content at the skill root read as `has_references=false`, which denies them the BP-007 sub-skill chunk and produces an under-structured draft.

**Fix:** `has_references_skill()` checks in this order:
1. `references/*.md` present → fire
2. Sibling `*.md` files at skill root (excluding `SKILL.md`) → fire
3. SKILL.md body has ≥200 non-empty lines → fire (proxy for inlined reference content)

**Fixture:** `fixtures/skills/sibling-refs-skill/` with `SKILL.md` + `editing.md`.

**Test:** `TestEdgeCase1SiblingRefs.test_sibling_md_fires_has_references`.

**Compliance side effect:** when the factory AUTHORS a skill, it still writes references into `references/` per BP-008. This edge case only matters for classifying existing skills during dogfood regeneration.

---

## Edge case 2 — Phase naming beyond "Phase N" / "Step N"

**Who:** `/411-research` uses `## Workflow` with a numbered list of 5 items inside the section. Strict `^#{2,4} (?:Phase|Step) \d+` misses it entirely and classifies the skill as `has_phases=false`.

**The naive mistake:** regex only for `Phase N` and `Step N` headings. Skills using `## Workflow`, `## Procedure`, `## 1. Foo`, or `## 1) Bar` are invisible.

**Fix:** `has_phases_any()` checks in this order:
1. ≥3 `## Phase N` / `## Step N` headings → fire
2. ≥3 numbered section headings (`## \d+[\.\)] \S`) → fire
3. `## Workflow` / `## Procedure` / `## Process` section with ≥3 numbered list items in first 50 lines → fire
4. Happy-path walkthrough section with ≥3 numbered list items → fire

**Fixture:** `fixtures/skills/workflow-section-skill/`.

**Test:** `TestEdgeCase2WorkflowSection.test_workflow_heading_fires_has_phases`.

---

## Edge case 3 — Skip gstack-style bash preamble when scanning `invokes_skills`

**Who:** `/retro`, `/plan-ceo-review`, `/office-hours`, `/checkpoint`, `/new-project`, and other gstack family skills open SKILL.md with 50+ lines of bash that include paths like `~/.claude/skills/gstack/bin/gstack-update-check`. Naive `/<skill-name>` regex matches `/gstack`, `/bin`, `/codex`, `/autoplan` inside those shell paths — producing false positives.

**The naive mistake:** scan the entire SKILL.md for `/<slug>\b`. Shell path fragments match and the classifier reports false invocations.

**Fix:** `_strip_gstack_preamble()` walks from the top of the file and, if preamble sentinels (`_FOO=...`, `source `, `eval "`, `if [ "$_`, `export FOO=...`) are detected above the first real Markdown H2-H3, strips everything before that H2. Invocation scanning happens against the stripped body only.

**Additional defense:** `invokes_skills_skill()` also strips fenced code blocks and inline code spans that contain file-path characters (`~`, `/bin/`, `/scripts/`) so even inline path fragments inside prose are ignored.

**Fixture:** `fixtures/skills/gstack-preamble-skill/` with a realistic bash preamble.

**Test:** `TestEdgeCase3GstackPreamble.test_preamble_does_not_trigger_invokes_skills`.

---

## Edge case 4 — Paired-family toggles don't count as `invokes_skills`

**Who:** `/freeze` references `/unfreeze` as its companion command. `/guard` composes `/careful + /freeze + /unfreeze` but does not spawn them as Agents. These are user-initiated counterparts, not Agent delegation.

**The naive mistake:** any `/<skill-name>\b` match fires `invokes_skills`. `/freeze` gets classified as `invokes_skills=true`, which triggers BP-023 (Agent composition) — the wrong sub-skill chunk for a standalone mode toggle.

**Fix:** `_PAIRED_FAMILY_BLOCKLIST` = `{freeze, unfreeze, careful, guard, unlock}`. Matches against any blocklisted name are recorded but excluded from the invocation set. The predicate fires only if there is a non-blocklisted match that also exists in the ecosystem.

**Fixture:** `fixtures/skills/paired-toggle-skill/` with `/unfreeze` in prose but no real Agent delegation.

**Test:** `TestEdgeCase4PairedToggle.test_paired_family_excluded_from_invokes_skills`.

**Maintenance note:** when new paired families appear in the ecosystem (e.g., a hypothetical `/lock + /unlock` pair), add both names to the blocklist AND document the pair here. Do NOT delete names from the blocklist without verifying no ecosystem skill has them as companions.

---

## Testing discipline

Every edge case above has:
- A fixture in `fixtures/skills/<name>/` that reproduces the real-world pattern.
- A test in `tests/test_trait_predicates.py` asserting the correct verdict.
- A row in `fixtures/expected-traits.md` documenting the expected outcome.

If a future matrix exercise surfaces a fifth edge case:
1. Add the fixture.
2. Add the expected-traits row.
3. Write the test (it should FAIL initially, proving the bug).
4. Fix the predicate until the test passes.
5. Document the case here.

Per BP-030 (pattern first, code second), the fixture and test come before the predicate change.
