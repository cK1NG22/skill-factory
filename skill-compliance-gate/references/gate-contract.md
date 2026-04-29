# Gate contract — what `skill-compliance-gate` checks

The gate is a hands-off wrapper around two check families. It produces a
binary verdict (pass / fail) with a machine-readable BLOCKER line on fail.

## Family 1 — the canonical 13-check skill-compliance audit

The gate subprocess-calls `~/.claude/skills/skill-compliance/scripts/compliance_check.py`.

The full 13-check matrix lives in `skill-compliance/SKILL.md`. For gate
purposes the checks partition into three verdict buckets:

| Severity       | Count | Gate effect |
|----------------|-------|-------------|
| `required`     |   6   | Any `fail` → gate **FAIL**. |
| `best-practice`|   7   | `warn` allowed; no gate effect. |
| `info`         |   1   | Body-size ideal-range marker; no gate effect. |

**Gate rule 1:** If the checker reports any check with `severity: required`
and `status: fail`, the gate emits BLOCKER. Required-tier FAILs are
structurally broken — missing SKILL.md, missing name, invalid kebab-case,
missing description, etc. A required FAIL means the assembled skill cannot
ship and no human triage is needed to see why.

**Gate rule 2:** Best-practice WARNs are tolerated. They exist to prod skill
authors toward a better shape, but they do not represent a structural
failure. Rolling a WARN into BLOCKER would stop too many legitimate runs.

## Family 2 — Check 14 (factory-specific): no meta-BP citations

A *client* skill (any skill the factory produces) must never cite the
factory's own internal best practices. Meta BPs (`bp-018`, `bp-025` through
`bp-034`) govern how the factory is built — thin drivers, sole human
touchpoints, BLOCKER conventions, pattern-first-code-second. They are not
general skill-authoring guidance. If a client skill cites them in its
`SKILL.md` or its `references/` tree, one of two things went wrong:

1. The **spec author leaked meta concerns** into a client-facing spec — the
   authored skill ended up describing factory mechanics to its end users.
2. The **factory's pack builder regressed** and included a meta-BP file path
   in the Tier-1/Tier-2 BP list for a client-facing sub-skill, which then
   surfaced in the generated `SKILL.md`.

Either way, the gate catches it before the skill ships. The Check 14 scan
has two hit patterns:

- **Path form**: the literal string `patterns/meta/bp-NNN` (with any three
  digits). Catches paths matching the template form
  `~/Projects/skill-factory/patterns/meta/bp-NNN-name.md` — the
  three-letter "NNN" placeholder is used here instead of a concrete
  digit-bearing example so this reference file itself stays clean under
  Stage 13 Check 15's `patterns/(meta/)?bp-\d{3}-name.md` regex.
- **Slug form**: any of the 11 current meta-BP slugs as a standalone word —
  `bp-018`, `bp-025`, `bp-026`, `bp-027`, `bp-028`, `bp-029`, `bp-030`,
  `bp-031`, `bp-032`, `bp-033`, `bp-034`. The match is case-insensitive
  and uses `\b` word boundaries, so inline mentions like ``` `bp-028` ```
  inside fenced code blocks still hit. That is intentional: a client skill
  should not be citing BP-028 at all, even inside a code block, because
  that tells the end user to think about the factory's BLOCKER convention
  rather than about their own domain.

**Gate rule 3:** Any Check 14 hit → gate **FAIL**. The initial plan staged
Check 14 as WARN-tier in Stage 10a and promotion to FAIL-tier in Stage 10b.
This file documents the **Stage 10a WARN posture**: hits are reported but
the code still treats them as BLOCKERs — the distinction between "WARN-tier
that blocks" and "FAIL-tier that blocks" is a labeling choice only. Stage
10b flips the documentation language without a code change.

## Scan surface

Check 14 scans four categories of files:

1. `<skill>/SKILL.md` — always scanned.
2. `<skill>/references/*` — every file one level deep. Nested subdirectories
   under `references/` are forbidden by BP-008, so the gate does not
   recurse into them (if they exist, the 13-check audit will already flag
   them via check #12 `references_depth`).
3. `<skill>/phases/*/director.md` — one per phase directory, when present.
4. `<skill>/phases/*/references/*` — one level deep inside each phase's
   per-phase `references/`, when present.

The gate does NOT scan:
- `scripts/` — code comments may legitimately reference factory BPs in
  TODO annotations; client-facing prose lives in `SKILL.md` and `references/`.
- `fixtures/` — fixtures are test data and are allowed to mention anything.
- `tests/` — same.
- `assets/` — static assets (images, templates); not prose surfaces.
- `output*` files inside `phases/*/` — per-phase Agent output artifacts.

## BLOCKER line format

On FAIL the gate writes one line to `notes.md`:

```
BLOCKER: compliance gate failed — <N> required-tier check(s) failed: <list>; <M> Check 14 meta-BP citation(s): <file:line (matched)>[, ...]
```

- Multiple failure classes are joined by `; `.
- Check 14 hits are truncated to the first 5 with a ` ...` marker when more
  exist, so the BLOCKER line stays readable.
- The driver copies this line verbatim to its own `notes.md` and STOPs
  before entering Phase 99 per BP-028.

## Hard precondition

The gate requires `~/.claude/skills/skill-compliance/scripts/compliance_check.py`
to exist. On miss, the gate emits `BLOCKER: skill-compliance not installed
at <path>` and STOPs. The gate does NOT attempt to locate the checker core
anywhere else — the path is authoritative per BP-031 (co-locate co-evolving
tools). A missing checker means a broken local install, not a gate bug.
