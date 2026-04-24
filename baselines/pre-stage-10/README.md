# Pre-Stage-10 Baselines

Snapshot of the factory's test / compliance / structural state captured on `main` at tip `e50513a`, 2026-04-24, immediately before Stage 10 work begins.

Purpose: Stage 10c's self-bootstrap verification (`self_bootstrap_diff.py`) is being extended with a **gate-verdict-match** invariant. It compares regenerated factory output against the committed factory and must show no compliance-verdict regression. These JSON files are the ground truth for that comparison. Stage 10b's Phase 8 wiring must also not regress any of the existing sub-skills' compliance verdicts.

Lighter than `pre-stage-9/` because Stage 10's change surface is smaller: one new sibling sub-skill (`skill-compliance-gate`), one new inline script (`assemble_skill.py`), one new phase directory (`phases/08-assemble-and-gate/`), and driver SKILL.md growing 8 → 9 Procedure steps. No source-tree restructure.

## Summary

### Tests (6 suites, 234 tests total, all green)

| Suite                                | Tests | Result |
|--------------------------------------|-------|--------|
| `skill-frontmatter/tests/`           |   22  | OK     |
| `skill-phase-designer/tests/`        |   33  | OK     |
| `skill-references-scaffolder/tests/` |   51  | OK     |
| `skill-cron-observability/tests/`    |   28  | OK     |
| `skill-signed-handoff/tests/`        |   36  | OK     |
| `skill-factory/tests/`               |   64  | OK     |
| **Total**                            |  **234** |       |

`skill-compliance` and `skill-spec-validator` intentionally have no `tests/` directories (checker script + validator-as-skill respectively).

Stage 10 target: 234 → ~304 across 8 suites (new `skill-compliance-gate/tests/` + 2 new factory test files + expansion of `test_build_context_pack.py`).

### Compliance (8/8 green, zero fails, zero warns)

| Skill                         | pass | fail | warn | skip | info |
|-------------------------------|------|------|------|------|------|
| `skill-compliance`            |  12  |  0   |  0   |  0   |  1   |
| `skill-cron-observability`    |  12  |  0   |  0   |  0   |  1   |
| `skill-factory` (driver)      |  12  |  0   |  0   |  0   |  1   |
| `skill-frontmatter`           |  13  |  0   |  0   |  0   |  0   |
| `skill-phase-designer`        |  12  |  0   |  0   |  0   |  1   |
| `skill-references-scaffolder` |  12  |  0   |  0   |  0   |  1   |
| `skill-signed-handoff`        |  12  |  0   |  0   |  0   |  1   |
| `skill-spec-validator`        |  12  |  0   |  0   |  0   |  1   |

Notable delta vs pre-Stage-9: `skill-factory` moved from `13/0/0/0/0` → `12/0/0/0/1`. The shift is body-size check #12 demoting from `pass` to `info` after the Stage 9.0.5 thin-director rewrite (149-line driver, below the compliance-ideal 180-220 band). Tracked as an open decision in HUB.md §Open decisions — "thin SKILL.md vs compliance ideal band" — and is an accepted state, not a regression.

### Driver SKILL.md snapshot

`snapshots/skill-factory-SKILL.md.original` — 149 body-lines. Captures the 8-step Procedure shape before Stage 10b adds Step 8 (Phase 8 — assemble + gate) and renumbers the old Step 8 (Phase 99 report) to Step 9. Acceptance: post-Stage-10b driver `SKILL.md` must stay below Principle E's ≤150 body-line target (or reliably under the ≤160 soft ceiling with orchestration prose pushed down into `phases/08-assemble-and-gate/director.md`).

## Verification gate for Stage 10 sub-commits

Each Stage 10 sub-commit must preserve **before** moving to the next sub-stage:

1. **All 6 existing test suites still `OK`** with unchanged counts (22, 33, 51, 28, 36, 64 = 234).
2. **Compliance on the 7 existing sub-skills + driver unchanged** — same `pass/fail/warn/skip/info` tallies per skill. (Check 14 meta-cite findings produced by the new `skill-compliance-gate` are out-of-scope of `compliance_check.py` itself and therefore not tallied here; they're captured separately in `gate.py`'s output.)
3. **Stage 10b only:** driver SKILL.md gains exactly one Procedure step (8 → 9) and stays phase-lint-clean + references-lint-strict-clean.

Stage 10c's `self_bootstrap_diff.py` extension will programmatically compare regenerated vs committed gate verdicts using these JSONs as the oracle.

## How to re-run a single baseline category

```bash
cd ~/Projects/skill-factory

# Tests (one suite):
(cd skill-<name> && python3 -m unittest discover tests 2>&1)

# Compliance against one skill tree:
python3 skill-compliance/scripts/compliance_check.py skill-<name>
```

## Rollback

Pre-Stage-10 uses the direct-on-main strategy (D7): no branch to delete. If any sub-stage must be abandoned, `git revert <stage-commit>` unwinds it. `baselines/pre-stage-10/` stays in history as an immutable reference.
