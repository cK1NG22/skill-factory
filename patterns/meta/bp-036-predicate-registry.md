# BP-036: Predicate registry for compound sub-skill triggers

**Source:** 2026-04-24 Stage 9b (skill-factory `_SUB_SKILL_TRIGGER_PREDICATE` registry + `skill-signed-handoff` AND-trigger); promoted from `feedback-predicate-registry-intersection-triggers.md`
**Category:** Driver gating (Meta — factory orchestration)

**Why:** When a sub-skill's firing condition is more than a single boolean trait — AND-intersection (`has_phases ∧ invokes_skills`), OR over mutually-exclusive traits, or any custom logic over trait evidence — embedding the predicate in a shell heredoc inside the driver SKILL.md is fragile, hard to test, and hidden from refactoring tools. The registry pattern keeps every compound predicate centralized in one Python `dict[str, Callable[[dict], bool]]`, unit-testable as ordinary functions, and greppable by name. The driver's gate becomes a single-line shell call to `--should-fire <sub-skill> <classifier.json>` whose exit code (0 = fire, 1 = skip, 2 = bad usage) controls flow. This is "Pattern B"; "Pattern A" is the inline single-trait gate used when no compound logic is needed.

**When applicable:** Sub-skills whose firing condition genuinely requires Python expressivity. For single-trait gates (the common case), Pattern A — a shell `if` against one trait field in `classifier.json` — is preferred and has less indirection. Pattern B is opt-in: sub-skills not registered in `_SUB_SKILL_TRIGGER_PREDICATE` are always-fireable from the helper's perspective, so registration is a deliberate choice. Most sub-skills will never need it.

**Enforced by:** `skill-factory/skill-factory/scripts/build_context_pack.py::_SUB_SKILL_TRIGGER_PREDICATE` (the registry itself), `should_fire(slug, classifier_dict)` helper, and the `--should-fire` CLI mode (exit codes 0/1/2). Pattern documentation lives at `skill-factory/skill-factory/phases/07-skill-signed-handoff/references/and-gating.md`. The driver's Phase 7 step calls the CLI rather than embedding the predicate inline.

**Correct:** `skill-signed-handoff` registers `lambda c: c["traits"]["has_phases"] and c["traits"]["invokes_skills"]` in `_SUB_SKILL_TRIGGER_PREDICATE`. Driver SKILL.md gate (one line): `if scripts/build_context_pack.py --should-fire skill-signed-handoff <classifier.json>; then ...`. The Python predicate is unit-tested in `tests/test_build_context_pack.py` alongside the rest of the helper.

**Incorrect:** Driver SKILL.md embeds a multi-line heredoc that runs `python3 -c "import json; c=json.load(open('classifier.json')); print(c['traits']['has_phases'] and c['traits']['invokes_skills'])"` and parses the output with `case`. The same logic is duplicated across two phase directors with no central source of truth and no test coverage.

**Cross-reference:** BP-033 (driver-materialized context packs — the registry is part of the driver's centralized control plane and ships in the same module that builds packs). BP-006 (lean traffic director — inline boolean Python in SKILL.md is a special case of fat-driver this BP cures).
