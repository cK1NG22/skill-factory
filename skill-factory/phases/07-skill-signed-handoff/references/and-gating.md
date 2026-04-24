# AND-gating via `_SUB_SKILL_TRIGGER_PREDICATE` (Pattern B)

Phase-scoped reference for Phase 7. Cited by `../director.md`.

This document captures the predicate-registry pattern introduced in
Stage 9b for `skill-signed-handoff` — the first sub-skill whose
trigger is an AND-intersection of two traits, not a single trait. The
pattern generalizes to any future sub-skill whose firing condition is
genuinely compound.

## Why a separate registry

The pre-Stage-9b factory used inline trait reads in the driver
SKILL.md to gate each conditional phase (Pattern A — single-trait OR
gate). Example (Phase 4 — phase-designer):

```bash
python3 -c "
import json, sys
traits = json.load(open('<work>/classifier.json'))['traits']
sys.exit(0 if traits.get('has_phases', {}).get('fires') else 1)
"
```

This works fine when the gate is a single boolean trait. It breaks
down when the gate is a compound expression — embedding non-trivial
boolean logic in a shell heredoc inside the driver SKILL.md is
fragile, hard to test, and hides the predicate from refactoring tools.

The Stage 9b solution: extract the predicate into a Python registry
in `build_context_pack.py` and expose it via a `--should-fire` CLI
mode that returns its verdict as an exit code. The driver SKILL.md's
gate becomes a single line:

```bash
python3 build_context_pack.py --should-fire <sub-skill-name> <classifier.json>
```

## How the registry works

`_SUB_SKILL_TRIGGER_PREDICATE` in `build_context_pack.py` is a
`dict[str, Callable[[dict], bool]]`. Each entry maps a sub-skill name
to a pure function over the classifier's `traits` dict:

```python
_SUB_SKILL_TRIGGER_PREDICATE = {
    "skill-signed-handoff": lambda t: (
        bool(t.get("has_phases", {}).get("fires"))
        and bool(t.get("invokes_skills", {}).get("fires"))
    ),
}
```

The `should_fire(sub_skill_name, classifier)` helper consults the
registry and returns:
- `True` if a registered predicate returns truthy.
- `True` if no predicate is registered for the sub-skill (the
  default-to-True invariant — most sub-skills don't need this
  registry, and the driver SKILL.md gates them via Pattern A).
- `False` if a registered predicate returns falsy.

The CLI mode wraps `should_fire` and converts the bool into exit
codes: `0 = fire`, `1 = skip`, `2 = bad usage`.

## When to use Pattern B vs Pattern A

| Trigger shape | Pattern | Where the gate lives |
|---|---|---|
| Single trait fires (e.g., `has_phases`) | A | Inline in driver SKILL.md |
| Always fires (e.g., frontmatter) | A (no gate at all) | Driver SKILL.md |
| AND of two+ traits (e.g., `has_phases ∧ invokes_skills`) | **B** | `_SUB_SKILL_TRIGGER_PREDICATE` |
| OR of mutually-exclusive traits | Either (prefer A if shape is simple) | Either |
| Custom logic over trait *evidence* (not just `fires`) | **B** | `_SUB_SKILL_TRIGGER_PREDICATE` |

Default to Pattern A. Reach for Pattern B only when the predicate
genuinely needs Python expressivity.

## Default-to-True invariant

A sub-skill not registered in `_SUB_SKILL_TRIGGER_PREDICATE` is
considered fireable by `should_fire`. This is intentional: most
sub-skills are gated by Pattern A in the driver SKILL.md, and the
predicate registry is opt-in. A sub-skill author who forgets to
register a predicate gets a sub-skill that always fires — which is
the correct fallback for a single-trait gate already enforced
elsewhere. Forgetting to gate at all (no Pattern A AND no Pattern B)
is a different bug, caught by the `## Adding a new sub-skill`
cheat-sheet checklist in the `build_context_pack.py` docstring.

## Future extensions (not Stage 9b scope)

- Migrating `skill-phase-designer` (single trait `has_phases`) to
  Pattern B is **anti-scope** — it would just be Pattern A wrapped in
  ceremony. Don't do it.
- Promoting Pattern B logic into a per-phase `gate.py` script
  (instead of all predicates living in `build_context_pack.py`) is a
  worth-considering refactor IF Stage 10+ adds 3+ more compound
  triggers. With one in Stage 9b, the centralized registry is fine.
