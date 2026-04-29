# BP-006: SKILL.md is a traffic director, sized by skill shape

**Source:** `tooling-skill-writing-patterns.md` (research-confirmed 2026-03-03); shape-aware reconciliation 2026-04-29 (Wave B, v1.1.1) per ADR-0002 Stage 14 follow-up
**Category:** File structure & references (Universal)

**Why:** Lazy-loading benefit lost if SKILL.md balloons. Detail belongs *outside* SKILL.md — in `references/` for single-Procedure skills, or in `phases/<N>-*/director.md` for phased orchestrators. Adding new content should never increase SKILL.md; it goes elsewhere. The Anthropic 500-line ceiling is the absolute max; the working target depends on the skill's *shape*.

**When applicable:** Every skill (Universal). The size target is shape-dependent — there are two canonical shapes:

- **Single-Procedure shape** (no `phases/<N>-*/director.md` sub-tree). The skill body holds one Procedure plus inline rationale; supporting detail in `references/`. Target: **180–220 body-lines** for complex multi-rule skills (phased-HITL, pipeline-orchestrator, research). Simple single-shot tools land at **100–150** and remain compliant. Most factory sub-skills (`skill-frontmatter`, `skill-phase-designer`, `skill-references-scaffolder`, `skill-cron-observability`, `skill-signed-handoff`, `skill-compliance-gate`, `skill-spec-validator`, `skill-compliance`) follow this shape.

- **Phased-orchestrator shape** (with `phases/<N>-*/director.md` sub-tree). The top SKILL.md is a numbered list of pointer-steps; per-phase mechanics live in the phase directors, not in the top file. Target: **≤150 top SKILL.md body-lines** per BP-037's thin-top-director discipline. The skill-factory driver is the canonical example (130 body-lines across 10 phases, with `phases/01-skill-frontmatter/director.md` ... `phases/99-report/director.md` carrying the per-phase logic).

The two shapes are mutually exclusive: a skill is either a single-Procedure leaf or a phased orchestrator. The presence of `phases/<N>-*/director.md` is the unambiguous discriminator.

**Enforced by:** `skill-references-scaffolder` (`references_lint --strict-two-level` walks the phase directors when the phased shape is detected); `skill-compliance` (the body-size check reports `info` rather than `fail` for thin top-directors below 180, recognizing the BP-037 carve-out).

**Correct (single-Procedure):** SKILL.md has 6 Procedure steps × ~25 lines each + frontmatter, landing in 180–220; detailed rubrics and rule contracts in `references/`.

**Correct (phased orchestrator):** Top SKILL.md is a numbered list of pointer-steps each one paragraph long, sitting at 130 body-lines; per-phase orchestration in `phases/<N>-*/director.md`; cross-phase mechanics in top-level `references/`. The skill-factory driver is the canonical example.

**Incorrect (single-Procedure):** SKILL.md is 600 lines because the author inlined rubrics, examples, and lookup tables instead of factoring them into `references/`.

**Incorrect (phased orchestrator):** Top SKILL.md is 250+ lines because per-phase mechanics were inlined instead of factored into phase directors. Adding a new phase becomes diff-noisy across the same big file, and the high-level orchestration shape gets lost in the detail.

**Cross-reference:** **BP-037** (thin-top-director — the phased-orchestrator branch of this BP, codifying ≤150 body-lines for top SKILL.md when `phases/` exists). BP-007 (references loaded on demand). BP-008 (references one level deep). BP-009 (parallel folders). BP-025 (siblings not nested).
