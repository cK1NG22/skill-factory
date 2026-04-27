# Pre-Stage-11 Baselines

Snapshot of the factory's test / gate-verdict / driver-shape state captured on `main` at tip `fe9b5b8`, 2026-04-27, immediately before Stage 11 (`materialize_skill.py` + Phase 9 wiring) work begins.

Purpose: Stage 11c's first-real-delivery verification step compares post-Stage-11 state against these baselines and must show:

1. **Tests** — 310 → ~349 (3 new test files; **0 pre-existing failures**, **0 unchanged-test count regressions**).
2. **Gate verdicts** — all 9 factory artifacts (incl. the driver itself) must STILL emit `verdict: pass` AND `meta_skill: true`. Stage 11 must not regress any artifact's gate verdict — the bonus-sweep invariant codified at Stage 10c is now load-bearing.
3. **Driver SKILL.md shape** — Phase 9 grows the Procedure 9 → 10 sequential steps. The body grows from 154 to ~165 body-lines. This breaches Principle E's ≤150-line target by ~15 lines (Q4 in plan v2 explicitly accepts this drift; a separate compaction stage is queued post-Stage-11). The byte-snapshot here is the diff oracle for that growth.

Lighter than `pre-stage-10/` because Stage 11's change surface is again small: one new inline script (`materialize_skill.py`), one new phase directory (`phases/09-materialize/`), a 10th driver Step, a new optional `## Delivery` section in the spec template, and per-client-repo / collaborator scaffolding. **No source-tree restructure.**

## Layout

Flat structure — 4 files at the top level (mirrors plan v2 §"Stage 11.0 — Pre-flight baselines"):

```
baselines/pre-stage-11/
├── README.md                       (this file)
├── tests-summary.txt               (310-test green snapshot, 7 suites)
├── gate-verdicts.json              (9-artifact gate verdicts, all PASS, all meta_skill:true)
└── skill-factory-skill-md.md       (byte-identical copy of skill-factory/SKILL.md @ fe9b5b8)
```

## Summary

### Tests (7 suites, 310 tests total, all green)

| Suite                                | Tests | Result |
|--------------------------------------|-------|--------|
| `skill-frontmatter/tests/`           |   22  | OK     |
| `skill-phase-designer/tests/`        |   33  | OK     |
| `skill-references-scaffolder/tests/` |   51  | OK     |
| `skill-cron-observability/tests/`    |   28  | OK     |
| `skill-signed-handoff/tests/`        |   36  | OK     |
| `skill-factory/tests/`               |  106  | OK     |
| `skill-compliance-gate/tests/`       |   34  | OK     |
| **Total**                            |  **310** |    |

`skill-compliance` and `skill-spec-validator` intentionally have no `tests/` directories (checker script + validator-as-skill respectively).

Stage 11 target: 310 → ~349 across 7 suites (no new sub-skill suites — Stage 11's deliverable is an inline script, not a new sub-skill, per D1 in plan v2).

### Gate verdicts (9/9 PASS, all meta_skill:true)

| Artifact                       | verdict | meta_skill |
|--------------------------------|---------|------------|
| `skill-compliance`             | pass    | true       |
| `skill-spec-validator`         | pass    | true       |
| `skill-frontmatter`            | pass    | true       |
| `skill-phase-designer`         | pass    | true       |
| `skill-references-scaffolder`  | pass    | true       |
| `skill-cron-observability`     | pass    | true       |
| `skill-signed-handoff`         | pass    | true       |
| `skill-compliance-gate`        | pass    | true       |
| `skill-factory` (driver)       | pass    | true       |

This is the steady-state shape since Stage 10c added the `meta-skill: true` frontmatter marker to all 9 factory artifacts. The gate auto-detects the marker via `is_meta_skill()` and skips Check 14 (meta-BP citation scanner), making every factory-internal artifact gate-clean. Stage 11 must preserve all 9 PASS verdicts — including the driver's own.

### Driver SKILL.md snapshot

`skill-factory-skill-md.md` — 164 file-lines (154 body-lines per `compliance_check.py` body-size check). Captures the 9-step Procedure shape on the day Stage 11.0 lands, before Stage 11b adds Step 9 (Phase 9 — materialize) and renumbers the old Step 9 (Phase 99 report) to Step 10.

Acceptance after Stage 11b:
- File-lines: ~175 (one new Step adds ~10 body-lines + a few separators).
- Body-lines: ~165 (over Principle E's ≤150 target — accepted per Q4 in plan v2; queued for compaction in a separate post-Stage-11 stage).
- Phase-lint: still clean, 10 sequential steps recognized.
- `references_lint.py --strict-two-level`: clean walk over 10 phase directors.

## Verification gate for Stage 11 sub-commits

Each Stage 11 sub-commit must preserve **before** moving to the next sub-stage:

1. **All 7 existing test suites still `OK`** — counts may grow only via the explicit Stage-11 test additions in `test_materialize_skill.py`, `test_build_context_pack.py` (+Phase 9 wiring), and `test_phase9_e2e.py`. No silent test-count regressions.
2. **Gate verdicts unchanged on all 9 artifacts** — every pre-existing artifact still emits `pass` + `meta_skill: true`. The driver's own gate verdict is the canary: if Stage 11b's SKILL.md growth breaks any check, the driver's gate flips first.
3. **Stage 11b only:** driver SKILL.md gains exactly one Procedure step (9 → 10), still phase-lint clean, still `references_lint --strict-two-level` clean over 10 phase directors.
4. **Stage 11c only:** end-to-end live run produces an installed skill at `~/.claude/skills/acme-board-memo/` symlinked to `~/Projects/acme-claude-skills/acme-board-memo/`. Smoke-test in a fresh `claude` session confirms the trigger phrases activate the new skill.

## How to re-run a single baseline category

```bash
cd ~/Projects/skill-factory

# Tests (one suite):
(cd skill-<name> && python3 -m unittest discover tests 2>&1)

# Gate verdict against one artifact:
python3 skill-compliance-gate/scripts/gate.py --skill skill-<name>

# All 9 in one shot (regenerate gate-verdicts.json):
python3 -c "
import json, subprocess
skills = ['skill-compliance', 'skill-spec-validator', 'skill-frontmatter',
          'skill-phase-designer', 'skill-references-scaffolder',
          'skill-cron-observability', 'skill-signed-handoff',
          'skill-compliance-gate', 'skill-factory']
out = {}
for s in skills:
    r = subprocess.run(['python3', 'skill-compliance-gate/scripts/gate.py', '--skill', s],
                       capture_output=True, text=True)
    out[s] = json.loads(r.stdout)
print(json.dumps(out, indent=2, sort_keys=True))
"
```

## Rollback

Pre-Stage-11 uses the direct-on-`main` strategy (D9): no branch to delete. If any sub-stage must be abandoned, `git revert <stage-commit>` unwinds it. `baselines/pre-stage-11/` stays in history as an immutable reference for any later post-mortem.
