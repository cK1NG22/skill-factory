# Stage 9.0.7 — Full baseline re-verification receipt

**Date:** 2026-04-24
**Branch:** `stage-9-work` at `aff31f7` (Stage 9.0.6 tip)
**Baseline captured:** Stage 9.-1 at `71a4fab` (from `main` tip `3c3b952`)

Re-ran every Stage 9.-1 baseline capture against the current tree and diffed output-by-output. Every delta below is one the Stage 9.0 plan explicitly accepts; nothing unexpected surfaced.

## Tests — 6 suites

| Suite | Baseline | Fresh | Delta | Status |
|-------|----------|-------|-------|--------|
| skill-cron-observability | 28 tests, OK | 28 tests, OK | timing only | ✅ identical (byte) |
| skill-factory | 38 tests, OK | 38 tests, OK | timing only (0.115→0.122s) | ✅ accepted (non-deterministic) |
| skill-frontmatter | 22 tests, OK | 22 tests, OK | timing only (0.078→0.072s) | ✅ accepted |
| skill-phase-designer | 33 tests, OK | 33 tests, OK | timing only (0.094→0.096s) | ✅ accepted |
| skill-references-scaffolder | 38 tests, OK | 51 tests, OK | **+13 tests** | ✅ accepted (+5 from 9.0.4 `--two-level`, +8 from 9.0.6 `--strict-two-level`) |
| skill-signed-handoff | 36 tests, OK | 36 tests, OK | timing only (0.123→0.129s) | ✅ accepted |

**Total:** 195 baseline → 208 fresh. 0 pre-existing fails changed, 0 new fails, 0 new skips.

## Lints — 23 baseline artifacts

| Artifact | Delta | Status |
|----------|-------|--------|
| skill-factory-phase.json | warns 1→0 (`"no '## Procedure' section header"` cleared); info `6 step(s)` → `5 step(s)` | ✅ accepted — SKILL.md rewrite in 9.0.5 added proper Procedure header and thinned step count |
| skill-factory-references.json | info `2 .md file(s)` → `5 .md file(s)` | ✅ accepted — cross-phase `references/` grew during 9.0.2 extraction |
| all 21 others | (none) | ✅ byte-identical |

No fails introduced anywhere. No warns introduced anywhere. All `passed: true` values preserved.

## Compliance — 8 skills

| Skill | Delta | Status |
|-------|-------|--------|
| skill-factory | body `201` → `113` lines (from SKILL.md rewrite in 9.0.5); body-size status `pass` → `info` (below 180-220 ideal, still within 500 max); references-density check → `not applicable` (body ≤ 200 lines); `passed: 13` → `12` | ✅ accepted — HANDOFF-documented: "1 check flipped to not applicable, body shrunk from 201→113 lines; 0 new fails" |
| all 7 others | (none) | ✅ byte-identical |

0 new fails across all 8 skills.

## Summary

- **Tests:** 1 count delta (accepted), 5 timing deltas (non-deterministic, accepted), 0 regressions.
- **Lints:** 2 field deltas in skill-factory (both accepted), 21 byte-identical.
- **Compliance:** 1 field delta in skill-factory (accepted), 7 byte-identical.
- **Snapshots:** `snapshots/skill-factory-SKILL.md.original` preserved as the pre-9.0.5 rollback copy; the live SKILL.md has moved to the thin-director form per 9.0.5.

**Verdict:** Stage 9.0 is fully verified. Ready for fast-forward merge to `main`.

## Re-run commands

Full sweep re-runs from the repo root:

```bash
# Tests
for s in skill-cron-observability skill-factory skill-frontmatter \
         skill-phase-designer skill-references-scaffolder skill-signed-handoff; do
  (cd "$s" && python3 -m unittest discover tests 2>&1 | tail -5)
done

# Lints (baseline-matching: no flags)
for s in skill-compliance skill-cron-observability skill-factory \
         skill-frontmatter skill-phase-designer skill-references-scaffolder \
         skill-signed-handoff skill-spec-validator; do
  python3 skill-frontmatter/scripts/frontmatter_lint.py "$s/SKILL.md"
  python3 skill-phase-designer/scripts/phase_lint.py "$s/SKILL.md"
  python3 skill-references-scaffolder/scripts/references_lint.py "$s"
done

# Strict-mode lint on the driver tree (new in 9.0.6)
python3 skill-references-scaffolder/scripts/references_lint.py skill-factory \
  --has-references --has-phases --two-level --strict-two-level

# Compliance
for s in skill-compliance skill-cron-observability skill-factory \
         skill-frontmatter skill-phase-designer skill-references-scaffolder \
         skill-signed-handoff skill-spec-validator; do
  python3 skill-compliance/scripts/compliance_check.py "$s"
done
```
