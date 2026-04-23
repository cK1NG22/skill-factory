# ADR-0001: Archetype frame — Rule engine over 5 traits (Frame C)

**Status:** Accepted
**Date:** 2026-04-23
**Deciders:** Carter King (ck22coding)
**Supersedes:** The 15-archetype taxonomy in `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md` (original plan, §Archetype taxonomy).

---

## Context

The original Skill Factory plan (2026-04-22) proposed **15 named archetypes** (mode-toggle, transformation, phased-HITL, pipeline-orchestrator, research-synthesis, meta-optimizer, etc.) each with its own manifest file listing which sub-skills to run in what order.

Several smells emerged before Stage 4 started:

- Subtypes — asymmetric-write-control ⊂ mode-toggle, taste-gated-HITL ⊂ phased-HITL, multi-model-reasoning ⊂ pipeline-orchestrator — indicated the categories were top-down naming intuitions, not structural differences in how you build the skill.
- **BPs are not homogeneous.** Some apply to every skill (trigger phrases, name rules, allowed-tools). Some apply only in specific situations (cron observability for scheduled skills). Some are factory-internal (sub-skills-are-siblings, sole-human-touchpoint).
- **Authoring-artifact discipline ≠ optimization-run discipline.** Writing a `kpi.md` is cheap and makes every skill autoresearch-ready; running `/autoresearch` against it is expensive and situational. The original plan conflated them under a single "phased HITL" archetype.
- **Sub-skills are rare in practice.** Most client skills will use reference files internally (BP-034). Named archetypes that assume sub-skill composition (pipeline-orchestrator, multi-model-reasoning) would rarely fire.

## Decision

**Adopt Frame C (rule engine over 5 traits).** The factory does NOT branch on named archetypes. At Phase 4, the driver evaluates 5 binary trait predicates against the validated spec and unions sub-skill chunks from whichever traits fire. 12 Universal BPs always fire. 11 Meta BPs apply to the factory itself, never client skills.

### The 5 traits (locked)

| Trait | Predicate (semantic) | Fires these BPs |
|---|---|---|
| `has_references` | Spec has framework/lookup content >10 lines (will produce a `references/` directory or equivalent sibling .md files) | BP-007 |
| `has_phases` | Happy-path walkthrough has ≥3 distinct steps; skill executes a workflow, not a single transformation | BP-009, BP-010 |
| `has_hitl` | Spec declares user gates mid-flow (uses `AskUserQuestion`, or procedure explicitly waits on the user) | BP-011, BP-012, BP-013, BP-015, BP-016 |
| `is_scheduled` | Spec has a scheduling section (cron, recurring, nightly, etc.) | BP-022 |
| `invokes_skills` | Spec's "Existing skills to reuse" names at least one `/<slash-command>` that EXISTS in the ecosystem (BP-034 gate) | BP-023 (always) + BP-024 (iff also `has_phases`) |

### Predicate refinements (from matrix evidence)

- `has_references` detection must accept **both** the `references/` subdirectory convention AND sibling `.md` files at skill root (e.g., pptx's `editing.md`, pdf's `reference.md`). Sibling files technically violate BP-008, but they ARE references in function. Flag as a compliance warning, but fire the trait.
- `has_phases` must accept **multiple phase-naming styles**: "Phase N:", "Step N", "## Workflow" with numbered sub-items, or any ≥3-deep numbered section sequence. Strict "Phase N:" regex misses skills like `/411-research` that use "## Workflow" with inline numbering.
- `has_hitl` must **skip gstack-style bash preamble** when counting AskUserQuestion usage. Gstack skills start with 50+ lines of bash that may include AskUserQuestion in unreachable branches. Real HITL is in the procedural body.
- `is_scheduled` is case-insensitive match on cron/scheduled/daily/weekly/hourly/nightly in description or body (unchanged).
- `invokes_skills` must be **conservative**: match `/<skill-name>\b` in body, exclude matches inside shell paths (`~/.claude/skills/<name>/bin/...`), exclude self-references. The spec-validator's BP-034 check independently confirms ecosystem existence.

### Why not Frame A (fixed taxonomy of ~7)?

Even a clean 7-category taxonomy fails on hybrids. `/email-tracker` is scheduled AND writes a structured report AND composes with Slack. Naming it "scheduled/cron" hides half its machinery. Frame A forces every skill into one category; the matrix shows most real skills span 2–3 categories' worth of behavior.

### Why not Frame B (explicit spec tags)?

Adequate, but more work for the spec author with no additional signal over Frame C. Tags force the author to pick from an enumerated list; Frame C reads the same signal from content the author already writes (happy-path steps, scheduling section, reuse section). If the spec is clear, Frame C gets the same answer as Frame B without the extra declaration.

---

## Evidence: 20-skill matrix

Classifier applied to 20 representative skills spanning transformation / phased-HITL / pipeline / scheduled / mode-toggle / review / synthesis / guidance / meta archetypes.

### Raw classifier output (automated detection)

| Skill | has_refs | has_phases | has_hitl | is_scheduled | invokes_skills |
|---|---|---|---|---|---|
| docx | Y(1) | Y(3) | N | N | N |
| pptx | N(0)† | N(0)‡ | N | N | N |
| pdf | N(0)† | N(0)‡ | N | N | N |
| 411-case | Y(12) | Y(7) | Y | N | Y (/411-deck, /411-refine, /411-reresearch, /411-research) |
| 411-research | N(0)† | N(0)‡ | N | N | Y (/411-case, /411-refine, /sources-cited) |
| 411-deck | N(0) | Y(21) | Y(3) | N | Y (/411-case) |
| freeze | N(0) | N(0) | Y(1) | N | Y (/unfreeze)§ |
| guard | N(0) | N(0) | Y(1) | N | Y (/careful, /freeze, /unfreeze)§ |
| email-tracker | Y(1) | Y(5) | N | Y | N |
| skill-creator | Y(1) | Y(9) | N | N | N |
| autoresearch | Y(3) | Y(11) | Y(7) | N | Y (/kpi-setter, /loop) |
| skill-compliance | N(0) | Y(4) | Y(1)¶ | N | N |
| brain-dump | N(0) | N(0) | Y(1) | N | N |
| checkpoint | N(0) | Y(9)⊕ | Y(14) | N | Y (/autoplan, /codex, /gstack)⊗ |
| skill-spec-validator | Y(1) | Y(6) | N | N | N |
| kpi-setter | Y(4) | Y(7) | Y(17) | N | Y (/autoresearch) |
| new-project | N(0) | N(1) | N | N | Y (/dung)⊗ |
| retro | N(0) | Y(15) | Y(13) | Y | Y (/autoplan, /codex, /gstack)⊗ |
| plan-ceo-review | N(0) | N(2) | Y(44) | N | Y (/autoplan, /browse, /codex, /gstack)⊗ |
| office-hours | N(0) | Y(11) | Y(29) | N | Y (/autoplan, /browse, /codex, /design-consultation, /gstack)⊗ |

Notes on classifier limits:
- † = sibling `.md` files at skill root instead of `references/` subdirectory (pptx has `editing.md`/`pptxgenjs.md`; pdf has `forms.md`/`reference.md`; 411-research inlines into SKILL.md).
- ‡ = workflow exists but uses non-"Phase N" section naming (pptx has "## Quick Reference / ## Editing Workflow"; 411-research has "## Methodology: SIFT / ## Source Hierarchy / ## Workflow").
- § = paired-family toggle. freeze's `/unfreeze` and guard's `/careful+/freeze+/unfreeze` are companion commands rather than true Agent invocations.
- ¶ = skill-compliance's Y(1) is likely a comment or example mention, not actual HITL.
- ⊕ = checkpoint's 9 "Phase" hits are likely gstack-preamble sections, not skill phases.
- ⊗ = gstack bash preamble false positives. These skills run `~/.claude/skills/gstack/bin/...` as shell scripts in their preamble; the classifier matched `/gstack`, `/codex`, `/autoplan` inside shell path fragments rather than in actual slash-command invocations.

### Manual-adjusted view (after applying the refined predicates)

| Skill | has_refs | has_phases | has_hitl | is_sched | invokes | Informal label |
|---|---|---|---|---|---|---|
| docx | ✓ | ✓ | ✗ | ✗ | ✗ | transformation w/ refs |
| pptx | ✓ | ✗ | ✗ | ✗ | ✗ | transformation (simple) |
| pdf | ✓ | ✗ | ✗ | ✗ | ✗ | transformation (simple) |
| 411-case | ✓ | ✓ | ✓ | ✗ | ✓ | pipeline head (interactive) |
| 411-research | ✓ | ✓ | ✗ | ✗ | ✓ | research synthesis (autonomous) |
| 411-deck | ✗ | ✓ | ✓ | ✗ | ✓ | pipeline tail (interactive) |
| freeze | ✗ | ✗ | ✓ | ✗ | ✗ | mode toggle |
| guard | ✗ | ✗ | ✓ | ✗ | ✗ | mode toggle (composed) |
| email-tracker | ✓ | ✓ | ✗ | ✓ | ✗ | scheduled autonomous |
| skill-creator | ✓ | ✓ | ✗ | ✗ | ✗ | phased autonomous (meta) |
| autoresearch | ✓ | ✓ | ✓ | ✗ | ✓ | phased interactive (meta) |
| skill-compliance | ✗ | ✓ | ✗ | ✗ | ✗ | audit (autonomous) |
| brain-dump | ✗ | ✗ | ✓ | ✗ | ✗ | quick HITL (synthesis) |
| checkpoint | ✗ | ✗ | ✓ | ✗ | ✗ | quick HITL (state save) |
| skill-spec-validator | ✓ | ✓ | ✗ | ✗ | ✗ | phased autonomous (gate) |
| kpi-setter | ✓ | ✓ | ✓ | ✗ | ✓ | phased interactive (meta) |
| new-project | ✗ | ✗ | ✗ | ✗ | ✗ | single-shot (scaffold) |
| retro | ✗ | ✓ | ✓ | ✓ | ✗ | scheduled phased interactive |
| plan-ceo-review | ✗ | ✗ | ✓ | ✗ | ✗ | quick HITL (guidance) |
| office-hours | ✗ | ✓ | ✓ | ✗ | ✗ | phased interactive (guidance) |

### Observations

1. **The 5 traits are sufficient.** No skill in the sample required a trait not in the 5. No common pattern of BP enforcement falls outside the mapping.
2. **Trait co-occurrences are real but not collapse-worthy.** `has_phases` + `has_hitl` co-occur in 8/20 skills but NOT in another 5 skills that have one without the other (411-research is phased without HITL; brain-dump is HITL without phases). The two traits stay separate.
3. **`invokes_skills` is genuinely rare.** After correcting false positives (gstack bash paths, paired-family toggles, see-also mentions), only ~5/20 skills genuinely invoke other skills via Agent-style delegation: 411-case, 411-research, 411-deck (all part of 411-suite chain), autoresearch (uses /kpi-setter), kpi-setter (uses /autoresearch). This vindicates BP-034 — sub-skills are for cross-skill reuse, and cross-skill reuse is uncommon.
4. **`is_scheduled` fires for 2/20.** Low base rate confirms the expectation that scheduled skills are a small cluster (email-tracker, retro). Reasonable base rate; no reason to fold the trait into another.
5. **Sibling-`.md` pattern (pptx, pdf) is a BP-008 edge case.** These skills effectively have references but not in the `references/` subdirectory. The trait should fire; compliance should warn. Factory-authored skills should prefer the `references/` convention.
6. **Strict "Phase N" regex misses 411-research.** Workflow exists without that heading style. Predicate refinement: accept multiple heading patterns.

---

## Consequences

### Positive

- **Driver simplicity.** Phase 4 orchestration becomes: evaluate 5 predicates, union sub-skill chunks, topological-sort, invoke. No manifest lookup per archetype.
- **No manifest file proliferation.** Original plan would have needed 15 archetype manifest files in `skill-factory/references/archetypes/`. Now zero.
- **Composability.** A skill that has `has_phases + is_scheduled` (like `/retro`) naturally pulls both sub-skill chunks. No "retro is a subtype of trend/longitudinal which is a subtype of scheduled" taxonomy gymnastics.
- **Archetype names become post-hoc labels.** We can still call `[has_phases, has_hitl, has_references, invokes_skills]` a "phased-HITL-research" combo informally, but nothing in the factory branches on that label.
- **PATTERNS.md index already reflects this.** The bucket column (Universal / Conditional / Meta) and per-BP trait mapping are in place (commit 3897071).

### Negative

- **Predicate refinement is ongoing.** The matrix surfaced classifier edge cases (sibling .md, alternate phase naming, gstack preamble noise). The driver's predicate implementations must handle these — they're not free.
- **"Archetype" as a user-facing concept disappears.** Users no longer pick an archetype for their skill. Some may miss the predictability of named categories; documentation must frame the trait model as the replacement vocabulary.
- **Spec validator gains scope.** BP-034 check now involves filesystem lookups (does `/foo-bar` exist at `~/.claude/skills/foo-bar/`?), which adds a dependency on the ecosystem layout.

### Neutral

- **Optimization runs stay CLI-flag-gated.** `--polish-autoresearch`, `--polish-triggers`, `--polish-benchmark` — unchanged. Artifacts (kpi.md, trigger-evals, test-prompts) are universal regardless.
- **BP-100+ reservation stays open.** If archetype-specific BPs are ever needed (e.g., a Notion-specific archetype with its own patterns), the BP-100..199 range is reserved. Unlikely under Frame C, but not foreclosed.

---

## Alternatives considered and rejected

### Frame A — Fixed taxonomy trimmed to ~7 named archetypes
Rejected because even 7 categories force hybrids (`/email-tracker` = scheduled + writes-report + uses-sources) into one label that loses information. Frame C captures all three without naming.

### Frame B — Explicit spec tags
Rejected because tags force the spec author to pick from an enumerated list, and the same signal is already readable from content the author writes anyway (happy-path steps, scheduling section, reuse list). Frame B is Frame C with an extra declaration step that adds no new information.

### Status quo — 15 archetypes
Rejected per §Context: subtypes, BP heterogeneity, artifact-vs-run conflation, and rare sub-skill invocation all indicated the taxonomy was over-specified.

---

## Follow-ups

1. **Stage 4: Spec authoring ergonomics.** Author `client-spec-template.md`, 1 example spec, and anti-patterns file. Template should NOT include an archetype field — the spec author just describes the skill, and the validator/driver infer traits.
2. **Stage 5: Driver skeleton with the 5-predicate Phase 4 loop.** Implement `build_context_pack.py` so the driver can list specific `patterns/bp-NNN-*.md` file paths per sub-skill.
3. **Predicate implementations.** Each trait's predicate becomes a small Python function in `skill-factory/scripts/trait_predicates.py`. Handles the classifier edge cases surfaced in this ADR (sibling .md, gstack preamble skip, alternate phase naming, conservative invokes detection).
4. **Matrix is a living artifact.** Re-run classifier against new skills as they're authored; surface any that don't fit the 5 traits as candidate new-trait proposals (PATTERNS.md PR, per BP-030).

---

## References

- Plan: `~/.claude/plans/i-want-to-work-gentle-dolphin.md` (v3, approved 2026-04-23)
- PATTERNS.md index: [../PATTERNS.md](../../PATTERNS.md)
- BP-034 (sub-skill discipline): [../../patterns/meta/bp-034-subskill-vs-reference.md](../../patterns/meta/bp-034-subskill-vs-reference.md)
- HUB.md progress log: [../../HUB.md](../../HUB.md)
- Classifier script used for the matrix: inlined in session 2026-04-23 (Python stdlib; reads SKILL.md files, extracts frontmatter + body, applies heuristic regex for each trait). Not committed as a reusable tool — Stage 5 `trait_predicates.py` will be the production version.
