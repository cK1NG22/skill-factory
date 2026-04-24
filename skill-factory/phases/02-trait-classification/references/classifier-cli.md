# Trait classifier CLI — modes, schema, edge cases

Phase-scoped reference for Phase 2. Cited by `../director.md`.

## Two invocation modes

### `spec` mode — the factory's primary use

```bash
python3 trait_predicates.py spec <spec-path>
```

Classifies a validated client spec. This is the mode Phase 2 uses. Input:
a `.md` file that has already passed `/skill-spec-validator`. Output: JSON
to stdout with the 5-trait verdict.

### `skill` mode — dogfood / regression use

```bash
python3 trait_predicates.py skill <skill-dir>
```

Classifies an existing skill directory. Used by the ADR-0001 matrix
exercise and any regression check against the ecosystem. Phase 2 does
NOT use this mode — the factory runs `spec` mode exclusively.

## Output schema

```json
{
  "traits": {
    "has_references":   {"fires": bool, "evidence": "short string"},
    "has_phases":       {"fires": bool, "evidence": "short string"},
    "has_hitl":         {"fires": bool, "evidence": "short string"},
    "is_scheduled":     {"fires": bool, "evidence": "short string"},
    "invokes_skills":   {"fires": bool, "evidence": "short string"}
  }
}
```

Each trait's `fires` boolean is what downstream conditional phases
branch on. The `evidence` field is for human debugging only; no phase
branches on it.

## The 4 documented edge cases

Per `../../references/trait-edge-cases.md` (the existing factory-level
edge-case reference that predates Stage 9's hierarchy adoption):

1. **Sibling `.md` files at skill root** do NOT fire `has_references`
   (those are README/SKILL.md-class files, not references).
2. **Alternate phase section naming** (`## Workflow`, `## Procedure`,
   numbered `## N. Foo`) all fire `has_phases`.
3. **Gstack-style bash preamble** is stripped before scanning for
   `/<skill>` patterns — otherwise cosmetic `/help` references in
   preamble would false-positive `invokes_skills`. (Gstack-family skills
   are scoped OUT of classifier correctness per Stage 5.1.)
4. **Paired-family toggles** (`freeze` / `unfreeze`, `careful` / `guard`)
   are on a blocklist — a skill referencing its paired twin does not
   fire `invokes_skills`.

## Exit codes

- `0` — classification succeeded; well-formed JSON on stdout.
- `1` — I/O error (spec path does not exist, directory missing for
  `skill` mode, etc.).
- `2` — bad usage (wrong mode, wrong number of args).

Phase 2 halts the factory on any non-zero exit.

## Determinism guarantee

Given the same input spec, the classifier produces byte-identical JSON
on every run. No timestamps, no randomness, no filesystem side-effects
(the classifier is pure on the text content of the spec). This is
important for Stage 9c's self-bootstrap verification — the classifier
must emit the same `classifier.json` for the factory's own spec every
time.
