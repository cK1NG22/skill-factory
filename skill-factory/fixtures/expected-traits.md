# Expected classifier outputs

For each fixture, this is the authoritative trait verdict the classifier must return. The `fires` column is what `test_trait_predicates.py` diffs against. Evidence strings may vary; only the boolean matters for test pass/fail.

## Spec-mode fixtures (classify_spec)

Tests run against a locally-staged ecosystem (temp dir with mock skill directories) so the BP-034 `invokes_skills` check is hermetic and does not depend on the user's live `~/.claude/skills/`.

| Fixture | has_references | has_phases | has_hitl | is_scheduled | invokes_skills | Reasoning |
|---|---|---|---|---|---|---|
| `specs/clean-transformation.md` | ✗ | ✗ | ✗ | ✗ | ✗ | No reference-content signals. Single-line walkthrough. No user gates. No schedule. Reuse section says `None`. |
| `specs/phased-hitl-with-reuse.md` | ✓ | ✓ | ✓ | ✗ | ✓ | Mentions "reference lookup table" and "reference framework" (has_references). 6 numbered steps (has_phases). Multiple "ask the user", "prompt the user", "wait for" signals (has_hitl). Lists `/docx` in reuse (invokes_skills — tests provide a mock `/docx` in the ecosystem). |
| `specs/scheduled-report.md` | ✗ | ✓ | ✗ | ✓ | ✗ | No reference-content signals. 6 numbered steps. No user gates. "Scheduling" section + "nightly", "recurring", "cron" keywords fire is_scheduled. Reuse says `None`. |

## Skill-mode fixtures (classify_skill)

Each fixture directory lives under `skills/<name>/`. Tests should classify each and diff verdicts against this table.

| Fixture | has_references | has_phases | has_hitl | is_scheduled | invokes_skills | Edge case exercised |
|---|---|---|---|---|---|---|
| `skills/sibling-refs-skill/` | ✓ | ✗ | ✗ | ✗ | ✗ | **Case 1**: `editing.md` at skill root (no `references/` dir) fires `has_references`. |
| `skills/workflow-section-skill/` | ✗ | ✓ | ✗ | ✗ | ✗ | **Case 2**: `## Workflow` with 5 numbered list items fires `has_phases` even without `## Phase N`. |
| `skills/gstack-preamble-skill/` | ✗ | ✗ | ✗ | ✗ | ✗ | **Case 3**: bash preamble contains `/gstack`, `/bin` paths; the preamble-strip step prevents false-positive invokes. No real slash-command invocations in the body. |
| `skills/paired-toggle-skill/` | ✗ | ✗ | ✓ | ✗ | ✗ | **Case 4**: body mentions `/unfreeze` as a companion command. Paired-family blocklist excludes it from `invokes_skills`. "Ask the user" signal fires `has_hitl` (this skill is a mode toggle like `/freeze`). |

## How tests use this table

1. Test setup stages a temp directory with a mock ecosystem containing only `/docx/` as a sibling to the fixture so that `invokes_skills_spec` can pass BP-034 without depending on the user's real ecosystem.
2. Each fixture is classified via the matching mode (`classify_spec` or `classify_skill`).
3. Every trait's `fires` boolean is diffed against the table above.
4. Any mismatch fails the test.

## Updating this file

If a predicate rule changes, update both `scripts/trait_predicates.py` AND this table in the same commit. Expected-output drift caught at test time is cheaper than drift caught in production.
