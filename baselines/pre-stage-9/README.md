# Pre-Stage-9 Baselines

Snapshot of the factory's test / lint / compliance / structural state captured on branch `stage-9-work` at tip `3c3b952` (main), 2026-04-24, before Stage 9.0 began.

Purpose: any Stage 9.0 sub-commit must re-produce these exact outputs (modulo file paths that change with the two-level hierarchy) before the sub-commit is considered green. Zero behavioral delta is the gate.

## Summary

### Tests (6 suites, 195 tests total, all green)

| Suite | Tests | Result |
|-------|-------|--------|
| `skill-cron-observability/tests/` | 28 | OK |
| `skill-factory/tests/` (driver) | 38 | OK |
| `skill-frontmatter/tests/` | 22 | OK |
| `skill-phase-designer/tests/` | 33 | OK |
| `skill-references-scaffolder/tests/` | 38 | OK |
| `skill-signed-handoff/tests/` | 36 | OK |

**Note:** `skill-phase-designer` has 33 tests, not 23 as the HUB's KPI line claims. Discrepancy is the Stage 7a fixup (`1a4944a`, "+10 regression tests") that was never reflected in the HUB counter. Flag for post-Stage-9 housekeeping.

`skill-compliance` and `skill-spec-validator` have no `tests/` directories by design (skill-compliance ships a single CLI script; skill-spec-validator is validator-as-skill with no bundled Python tests — its fixtures + oracles live under `fixtures/`).

### Frontmatter lint (8/8 green)

Every sub-skill's `SKILL.md` passes `skill-frontmatter/scripts/frontmatter_lint.py` cleanly.

### Phase lint (3/8 green — 5 pre-existing fails)

**These are NOT Stage 9 regressions. They predate this branch.** Baseline records them so Stage 9.0's verification gate can distinguish "same pre-existing condition" from "new regression."

| Skill | Result | Pre-existing issue |
|-------|--------|--------------------|
| `skill-cron-observability` | PASS | — |
| `skill-references-scaffolder` | PASS | — |
| `skill-signed-handoff` | PASS | — |
| `skill-compliance` | FAIL | No `## Procedure` section (skill-compliance is a pure tool, not a procedural skill). |
| `skill-factory` (driver) | FAIL | 2 weak-voice instances ('attempt to', 'try to') in "What to do if you're stuck" — outside Procedure bounds, flagged in Stage 7b HUB log. |
| `skill-frontmatter` | FAIL | 4 imperative-verb violations (steps 4/5/6/10 start with 'where'/'structure'/'infer'/'contains') + 1 weak voice ('attempt to'). |
| `skill-phase-designer` | FAIL | 4 weak-voice instances ('it should', 'should be', 'we should', 'you should'). |
| `skill-spec-validator` | FAIL | 1 imperative-verb violation (step 6 starts with 'produce') + 1 weak voice ('should be') + no `## Procedure` heading (uses unnumbered sub-sections). |

### References lint (7/7 green — skill-compliance has no `references/` dir so N/A)

Every skill with a `references/` directory passes flat-mode references lint. The flat baseline is important because Stage 9.0.6 flips lint to strict two-level mode — leaf sub-skills must STILL pass after the flip (strict mode is a no-op for single-phase skills).

### Compliance (8/8 green, 0 fails total)

| Skill | pass | fail | warn | skip | info |
|-------|------|------|------|------|------|
| `skill-compliance` | 12 | 0 | 0 | 0 | 1 |
| `skill-cron-observability` | 12 | 0 | 0 | 0 | 1 |
| `skill-factory` | 13 | 0 | 0 | 0 | 0 |
| `skill-frontmatter` | 13 | 0 | 0 | 0 | 0 |
| `skill-phase-designer` | 12 | 0 | 0 | 0 | 1 |
| `skill-references-scaffolder` | 12 | 0 | 0 | 0 | 1 |
| `skill-signed-handoff` | 12 | 0 | 0 | 0 | 1 |
| `skill-spec-validator` | 12 | 0 | 0 | 0 | 1 |

### Driver SKILL.md snapshot

`snapshots/skill-factory-SKILL.md.original` — 211 lines. The Stage 9.0.5 rewrite must leave this byte-copy untouched for rollback purposes. Target post-rewrite: ≤40 lines under `skill-factory/SKILL.md` with extracted content living under `phases/<N>/director.md` + cross-phase `references/`.

## Verification gate for Stage 9.0 sub-commits

Each sub-commit must satisfy BEFORE the next sub-commit begins:
1. All 6 test suites still `OK`, test counts unchanged.
2. All 8 frontmatter-lint results still `passed: true`.
3. Phase-lint results match the baseline exactly — the 3 green skills stay green; the 5 pre-existing-fail skills still fail with the SAME fail reasons (no new fails, no silently fixed old fails — a "fix" is a Stage 9 non-goal).
4. References-lint: 7/7 still pass in flat mode through 9.0.5; after 9.0.6 strict-mode flip, all 7 still pass (leaf skills are no-op, driver tree passes strict).
5. Compliance: 8/8 still show zero fails.

## How to re-run a single baseline category

```bash
cd ~/Projects/skill-factory

# Tests (one skill):
(cd skill-<name> && python3 -m unittest discover tests 2>&1)

# Frontmatter lint against a SKILL.md:
python3 skill-frontmatter/scripts/frontmatter_lint.py skill-<name>/SKILL.md

# Phase lint against a SKILL.md:
python3 skill-phase-designer/scripts/phase_lint.py skill-<name>/SKILL.md

# References lint against a skill tree:
python3 skill-references-scaffolder/scripts/references_lint.py skill-<name>

# Compliance against a skill tree:
python3 skill-compliance/scripts/compliance_check.py skill-<name>
```

## Rollback

This entire directory lives on `stage-9-work`. If Stage 9.-1 or any later sub-stage needs to be abandoned, `git checkout main && git branch -D stage-9-work` deletes everything. `main` is untouched.
