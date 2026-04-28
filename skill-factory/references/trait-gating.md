# Trait-gated conditional phase entry

Cross-phase reference shared by every conditional phase director (any
phase that does not always fire). Used by Phase 4 (`skill-phase-designer`),
Phase 5 (`skill-references-scaffolder`), Phase 6 (`skill-cron-observability`),
and Phase 7 (`skill-signed-handoff`). Phases 1, 2, 3, and 99 always fire
and do not use this reference.

## The classifier.json contract

Phase 2 produces `<work>/classifier.json` with this shape:

```json
{
  "traits": {
    "has_references":   {"fires": true|false, "evidence": "…"},
    "has_phases":       {"fires": true|false, "evidence": "…"},
    "has_hitl":         {"fires": true|false, "evidence": "…"},
    "is_scheduled":     {"fires": true|false, "evidence": "…"},
    "invokes_skills":   {"fires": true|false, "evidence": "…"}
  }
}
```

Each phase director that conditionally fires reads ONLY `<trait>.fires`
from this JSON. The `evidence` field is for human debugging; the driver
does not branch on it.

## The three gating patterns

### Pattern A — single-trait OR gate

Used by Phase 4 (fires when `has_phases`) and will be used by Phase 5
(fires when `has_references`) and Phase 6 (fires when `is_scheduled`).

```bash
python3 -c "
import json, sys
traits = json.load(open('<work>/classifier.json'))['traits']
sys.exit(0 if traits.get('<trait-name>', {}).get('fires') else 1)
"
```

Exit 0 → enter phase. Exit 1 → skip phase and continue to next.

### Pattern B — AND-intersection gate

Used by Phase 7 only (fires when `has_phases` ∧ `invokes_skills`). Will be
implemented via the `_SUB_SKILL_TRIGGER_PREDICATE` registry in
`build_context_pack.py` during Stage 9b. Until then, Phase 7 does not exist.

When the registry is live, the gate is a single CLI call:

```bash
python3 scripts/build_context_pack.py \
    --should-fire skill-signed-handoff <work>/classifier.json
```

Exit 0 → enter phase. Exit 1 → skip.

Pattern B is the canonical implementation of BP-036 (predicate registry
for compound sub-skill triggers) — the registry is `_SUB_SKILL_TRIGGER_PREDICATE`
in `scripts/build_context_pack.py`; see `patterns/meta/bp-036-predicate-registry.md`
for when to choose Pattern B over Pattern A.

### Pattern C — no gate (always fires)

Phases 1, 2, 3, and 99 always fire. No conditional entry; their directors
do not reference this file.

## Universal + conditional BP union

The Phase 2 output also implicitly governs the BP union each downstream
sub-skill applies. See `scripts/build_context_pack.py`'s registries:

- `_SUB_SKILL_BPS` — always-applied BPs per sub-skill.
- `_SUB_SKILL_CONDITIONAL_BPS` — trait-gated BP additions (e.g. HITL adds
  BP-011/012/013/015/016 for `skill-phase-designer`).

Phase directors do not need to know the union rules — `build_context_pack.py`
computes them and materializes the unioned BP list into the sub-skill's
`input.md`.

## What the driver does NOT do

- Does NOT override a classifier verdict. If `has_phases.fires` is `false`,
  the phase is skipped even if the spec's walkthrough looks structured — the
  classifier is the single source of truth.
- Does NOT re-classify. Phase 2 runs exactly once per factory invocation.
- Does NOT treat an absent trait key as `true`. Missing key → treat as
  `fires: false` (safe default: skip the phase).
