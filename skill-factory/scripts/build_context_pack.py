#!/usr/bin/env python3
"""
build_context_pack.py — Phase 3 of the Skill Factory.

Takes a validated client spec and the Phase 2 classifier JSON output and
materializes `input.md` in the exact shape a sub-skill expects. This script
is the lone bridge between the driver's classifier and any sub-skill's
isolated Agent subtask — per BP-033, sub-skills read ONLY their `input.md`.

Usage:
    build_context_pack.py <spec-path> <classifier-json> <sub-skill-name> <out-dir>
        [--patterns-root <dir>] [--target-skill-dir <dir>]

    build_context_pack.py --prescaffold-references <spec-path> <target-skill-dir>

    build_context_pack.py --should-fire <sub-skill-name> <classifier-json>

Currently supported <sub-skill-name> values:
    skill-frontmatter
    skill-phase-designer
    skill-references-scaffolder    (Stage 9a)
    skill-cron-observability       (Stage 9a)
    skill-signed-handoff           (Stage 9b — AND-intersection trigger)

Output:
    <out-dir>/input.md — the materialized context pack.

Exit codes:
    0 — pack materialized successfully (or prescaffold completed, or sub-skill should fire)
    1 — spec missing a required section, sub-skill name unsupported, or sub-skill should NOT fire
    2 — usage / I/O error

## Adding a new sub-skill (author-facing cheat sheet)

To register a new sub-skill (e.g. Wave 3's skill-references-scaffolder), add a
row keyed by the sub-skill name in each applicable dict below. Two tiers:

  Tier 1 — always edit (4 dicts, Stage 6b baseline):
    1. _SUB_SKILL_BPS            — base BP filenames (always shipped)
    2. _SUB_SKILL_SECTIONS       — base spec sections to carry into input.md
    3. _SUB_SKILL_OUTPUT_BLURB   — where the sub-skill writes its outputs
    4. _SUB_SKILL_TASK           — one-line task statement

  Tier 2 — edit only if the sub-skill has trait-gated additions (2 dicts,
  Stage 7b extension):
    5. _SUB_SKILL_CONDITIONAL_BPS      — {trait: [bp-files]} — BPs added
                                         when the named trait fires
    6. _SUB_SKILL_CONDITIONAL_SECTIONS — {trait: [section-names]} — spec
                                         sections added when trait fires

If the sub-skill's BP list or section list never varies with traits, skip
Tier 2 entirely. The union with firing traits happens inside `build_pack` /
`resolve_bp_paths` — callers don't need to know about the split.

  Tier 3 — edit only if the sub-skill's trigger is NOT a single-trait OR-gate
  (1 dict, Stage 9b extension):
    7. _SUB_SKILL_TRIGGER_PREDICATE — {sub-skill-name: callable(traits) -> bool}.
                                      Pure function over the classifier's
                                      `traits` dict. Used by `should_fire()` to
                                      decide whether the driver enters the
                                      sub-skill's phase.

The default-to-True invariant: a sub-skill NOT registered in
_SUB_SKILL_TRIGGER_PREDICATE is always considered fireable — the driver
SKILL.md gates entry via inline trait reads (Pattern A in trait-gating.md).
Register here only when the trigger is genuinely compound (e.g., AND of
two traits, like `skill-signed-handoff` which fires only when
`has_phases ∧ invokes_skills`). Single-trait sub-skills (frontmatter
always, phase-designer on `has_phases`, refs on `has_references`, cron on
`is_scheduled`) skip Tier 3 — their gates already live in the driver.

## Pre-scaffolding (Stage 9a, skill-references-scaffolder only)

`skill-references-scaffolder` is a verifier — it walks an existing target
skill directory and lints its references/ tree. In driver mode, the target
skill does not yet exist. The driver therefore pre-scaffolds the target tree
from the spec before invoking the sub-skill: empty `references/<name>.md`
files (one per spec entry under "Reference exemplars") plus a stub
`SKILL.md` containing one canonical `Read references/<name>.md for ...` line
per entry. The sub-skill then verifies the populated tree.

The `prescaffold_references()` helper performs this. The Phase 5 director
calls it before invoking the sub-skill. The `--prescaffold-references` CLI
mode exposes it for direct testing.

The `--target-skill-dir <dir>` CLI flag (and matching `target_skill_dir`
parameter on `build_pack`) appends a `## Target skill directory` block to
`input.md`, supplying the sub-skill with the absolute path to walk.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable

# --- Universal + Conditional BP lookup per sub-skill ---
# Each sub-skill has its own canonical list of BPs. The frontmatter sub-skill
# uses the 5 frontmatter Universals (BP-001..BP-005). skill-phase-designer
# always carries BP-010 (apply-once / carry-forward, the numbering + sequencing
# rule), and when `has_hitl` fires it also carries BP-011/012/013/015/016.
#
# Trait-gated conditional BPs live in `_SUB_SKILL_CONDITIONAL_BPS` keyed by the
# trait name that activates them. `build_pack` unions the base list with any
# trait-gated lists whose trait fires in the classifier JSON.
_SUB_SKILL_BPS: dict[str, list[str]] = {
    "skill-frontmatter": [
        "bp-001-trigger-phrases.md",
        "bp-002-pushy-description.md",
        "bp-003-name-rules.md",
        "bp-004-description-length.md",
        "bp-005-allowed-tools.md",
    ],
    "skill-phase-designer": [
        "bp-010-apply-once-carry-forward.md",
    ],
    # Stage 9a: BP-007 (cited-on-demand) + BP-008 (one-level-deep) always
    # ship for refs-scaffolder. BP-009 (parallel folders) only when has_phases
    # also fires — see _SUB_SKILL_CONDITIONAL_BPS.
    "skill-references-scaffolder": [
        "bp-007-references-loaded-on-demand.md",
        "bp-008-references-one-level-deep.md",
    ],
    # Stage 9a: BP-022 is the cron-observability contract; BP-021 (output
    # home `~/Claude/<skill>/`) is the path-shape companion. Both ship
    # unconditionally because the sub-skill always reasons about both.
    "skill-cron-observability": [
        "bp-022-cron-observability.md",
        "bp-021-output-home.md",
    ],
    # Stage 9b: BP-024 is the signed-handoff contract (sha256 over the
    # argument-bearing fields). Meta BPs (BP-028, BP-033) are factory-internal
    # discipline the sub-skill self-applies via its own SKILL.md — not
    # shipped in the pack, consistent with frontmatter / phase-designer
    # which also self-apply BP-028 without the driver injecting it.
    "skill-signed-handoff": [
        "bp-024-signed-handoffs.md",
    ],
}

# Conditional BPs keyed by trait; unioned into the pack when the trait fires.
# Kept separate from `_SUB_SKILL_BPS` so the base list stays static — the
# `build_pack` call-site does the trait-gated union.
_SUB_SKILL_CONDITIONAL_BPS: dict[str, dict[str, list[str]]] = {
    "skill-phase-designer": {
        "has_hitl": [
            "bp-011-announce-phase-transitions.md",
            "bp-012-hard-gates.md",
            "bp-013-ask-user-first.md",
            "bp-015-number-questions.md",
            "bp-016-inline-question-rule.md",
        ],
    },
    # Stage 9a: parallel folders rule fires only when the target skill is
    # itself phased — i.e. when both has_references AND has_phases fire.
    # has_references is the trigger trait for the sub-skill itself; has_phases
    # is the conditional that pulls in BP-009.
    "skill-references-scaffolder": {
        "has_phases": [
            "bp-009-parallel-folders.md",
        ],
    },
}

# --- Sections each sub-skill needs from the spec ---
# Keeping packs narrow keeps sub-skill reasoning honest — don't ship sections
# the sub-skill does not use. Base sections always ship; trait-gated sections
# (e.g. HITL-relevant scoping) live in `_SUB_SKILL_CONDITIONAL_SECTIONS`.
_SUB_SKILL_SECTIONS: dict[str, list[str]] = {
    "skill-frontmatter": [
        "Company",
        "Skill slug",
        "One-line description",
        "Trigger phrases",
        "Inputs",
        "Outputs",
        "Happy-path walkthrough",
        "Anti-goals",
    ],
    "skill-phase-designer": [
        "Company",
        "Skill slug",
        "One-line description",
        "Inputs",
        "Outputs",
        "Happy-path walkthrough",
        "Failure modes",
        "Existing skills to reuse",
    ],
    # Stage 9a: refs-scaffolder needs the spec's references list (carried as
    # the optional "Reference exemplars" section per the spec template) plus
    # the walkthrough so citation targets make sense in context.
    "skill-references-scaffolder": [
        "Company",
        "Skill slug",
        "One-line description",
        "Reference exemplars",
        "Happy-path walkthrough",
    ],
    # Stage 9a: cron sub-skill consumes the Scheduling section to extract
    # cron frequency + artifact extension; Outputs to know where the
    # artifact ultimately lands; Failure modes to mirror in the result.json
    # `success: false` path.
    "skill-cron-observability": [
        "Company",
        "Skill slug",
        "One-line description",
        "Inputs",
        "Outputs",
        "Scheduling",
        "Happy-path walkthrough",
        "Failure modes",
    ],
    # Stage 9b: signed-handoff sub-skill needs the reuse section (to bind
    # upstream/downstream skill slugs), the walkthrough (for context on the
    # handoff sequence), and Failure modes (for the exit-code mapping). Two
    # custom optional sections — Pipeline composition + Argument-bearing
    # fields — are carried when the spec declares them, silently skipped
    # otherwise (per build_pack's missing-section coalesce). Specs that fire
    # the AND-trigger are expected to declare both, but the sub-skill
    # BLOCKERs cleanly at its Step 4 if the field list is absent.
    "skill-signed-handoff": [
        "Company",
        "Skill slug",
        "One-line description",
        "Existing skills to reuse",
        "Happy-path walkthrough",
        "Failure modes",
        "Pipeline composition",
        "Argument-bearing fields",
    ],
}

# Conditional sections keyed by trait; appended when the trait fires. These are
# sections the sub-skill only needs under specific trait conditions (e.g. the
# HITL sub-skill flow reads scoping-adjacent sections).
_SUB_SKILL_CONDITIONAL_SECTIONS: dict[str, dict[str, list[str]]] = {
    "skill-phase-designer": {
        "has_hitl": [
            "Success signals",
            "Edge cases",
        ],
    },
}

# --- Trigger predicate registry (Stage 9b — Tier 3) ---
# A sub-skill registered here fires only when its predicate returns True given
# the classifier's `traits` dict. A sub-skill NOT registered here fires
# unconditionally — the driver SKILL.md gates entry via inline trait reads
# (Pattern A in trait-gating.md). Register only for compound triggers (e.g.,
# the AND-intersection of has_phases ∧ invokes_skills used by signed-handoff).
_SUB_SKILL_TRIGGER_PREDICATE: dict[str, Callable[[dict], bool]] = {
    "skill-signed-handoff": lambda t: (
        bool(t.get("has_phases", {}).get("fires"))
        and bool(t.get("invokes_skills", {}).get("fires"))
    ),
}


def should_fire(sub_skill_name: str, classifier: dict) -> bool:
    """Decide whether `sub_skill_name` should run given the classifier output.

    Default-to-True invariant: a sub-skill not registered in
    _SUB_SKILL_TRIGGER_PREDICATE is always fireable from this helper's
    perspective — the driver SKILL.md's inline trait read is the gate. Use
    this helper only for AND-intersection (or other compound) triggers.

    Raises ValueError on unknown sub-skill, matching `build_pack` /
    `resolve_bp_paths`."""
    if sub_skill_name not in _SUB_SKILL_BPS:
        raise ValueError(
            f"unsupported sub-skill: {sub_skill_name!r}. "
            f"supported: {sorted(_SUB_SKILL_BPS.keys())}"
        )
    traits = classifier.get("traits") or {}
    predicate = _SUB_SKILL_TRIGGER_PREDICATE.get(sub_skill_name, lambda _: True)
    return bool(predicate(traits))


# --- Output location blurbs per sub-skill ---
_SUB_SKILL_OUTPUT_BLURB: dict[str, str] = {
    "skill-frontmatter": (
        "Write into the directory containing this `input.md`:\n"
        "- `output.yaml` — the raw frontmatter block (between `---` delimiters), parseable.\n"
        "- `output.md` — frontmatter + a `## Rationale` section explaining name/tools/trigger-order decisions.\n"
        "- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.\n"
        "\n"
        "Do NOT read any files not listed above. Do NOT open `patterns/` directly — "
        "the BP files you need are the ones listed above."
    ),
    "skill-phase-designer": (
        "Write `output.md` (draft ## Procedure section) and `notes.md` to `phases/02-skill-phase-designer/`.\n"
        "\n"
        "- `output.md` — the draft `## Procedure` section ready to paste into the target SKILL.md.\n"
        "- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.\n"
        "\n"
        "Do NOT read any files not listed above. Do NOT open `patterns/` directly — "
        "the BP files you need are the ones listed above."
    ),
    "skill-references-scaffolder": (
        "Write into the directory containing this `input.md`:\n"
        "- `output.md` — the scaffolder's plan: citation lines, BP-008 violations (if any), "
        "BP-009 parallel-folder verdict (if `has_phases` fires), and orphan files (present on disk "
        "but absent from the spec).\n"
        "- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.\n"
        "\n"
        "The driver has pre-scaffolded the target skill directory: empty `references/<name>.md` "
        "files (one per spec entry) plus a stub `SKILL.md` with one canonical citation line per file. "
        "Walk the populated tree and verify per the rules.\n"
        "\n"
        "Do NOT read any files not listed above. Do NOT open `patterns/` directly — "
        "the BP files you need are the ones listed above."
    ),
    "skill-cron-observability": (
        "Write into the directory containing this `input.md`:\n"
        "- `instrumentation-snippet.md` — a single fenced Python block ready to paste into the "
        "target skill's cron orchestration. Implements BP-022 Rules A–D.\n"
        "- `output.md` — rationale wrapper: the snippet plus one sentence per rule explaining "
        "how the snippet satisfies it.\n"
        "- `notes.md` — `BLOCKER:` lines if any, otherwise short informational observations.\n"
        "\n"
        "Do NOT read any files not listed above. Do NOT open `patterns/` directly — "
        "the BP files you need are the ones listed above."
    ),
    "skill-signed-handoff": (
        "Write into the directory containing this `input.md`:\n"
        "- `output-signature-template.py` — the stamped signature script ready to drop into the "
        "target skill's `scripts/` directory. Stamped from "
        "`/Users/carterking/Projects/skill-factory/skill-signed-handoff/scripts/signature-template.py` "
        "with the spec's argument-bearing fields list.\n"
        "- `notes.md` — `BLOCKER:` lines if any, otherwise short observations (declared SIGNED_FIELDS, "
        "upstream/downstream phase bindings).\n"
        "\n"
        "Do NOT read any files not listed above. Do NOT open `patterns/` directly — "
        "the BP files you need are the ones listed above."
    ),
}

# --- Task lines per sub-skill ---
_SUB_SKILL_TASK: dict[str, str] = {
    "skill-frontmatter": (
        "Generate compliant YAML frontmatter for a factory-authored skill. "
        "Write `output.yaml`, `output.md`, and `notes.md` into the same directory as this `input.md`."
    ),
    "skill-phase-designer": (
        "Design the ## Procedure section for the target SKILL.md. Pass scripts/phase_lint.py."
    ),
    "skill-references-scaffolder": (
        "Verify the pre-scaffolded references/ tree and emit the scaffolder's plan. "
        "Pass scripts/references_lint.py against the target skill directory."
    ),
    "skill-cron-observability": (
        "Generate a BP-022-compliant instrumentation snippet for the target cron skill. "
        "Pass scripts/observability_lint.py against the generated snippet."
    ),
    "skill-signed-handoff": (
        "Stamp a `<slug>_signature.py` script for the upstream skill's terminal phase, signing the "
        "argument-bearing fields declared in the spec. Pass scripts/handoff_lint.py against the stamped script."
    ),
}


# --- Markdown section parser (flat H2 split) ---

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_spec_sections(spec_text: str) -> dict[str, str]:
    """Split a client spec by H2 headings into {section_name: body}. Ignores
    the H1 title and any leading preamble (comments, intro paragraphs)."""
    sections: dict[str, str] = {}
    matches = list(_H2_RE.finditer(spec_text))
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(spec_text)
        body = spec_text[start:end].strip()
        sections[name] = body
    return sections


# --- Reuse-block parser (pulls /<slug> names for the traits block) ---

_SLASH_SKILL = re.compile(r"(?<![a-zA-Z0-9_/])/([a-z][a-z0-9-]{1,63})\b")


def extract_invoked_slugs(reuse_section_text: str | None) -> list[str]:
    if not reuse_section_text:
        return []
    if re.search(r"^\s*none\s*$", reuse_section_text.strip(), re.IGNORECASE | re.MULTILINE):
        return []
    return sorted(set(_SLASH_SKILL.findall(reuse_section_text)))


# --- Trait-block renderer ---


def render_traits_block(classifier: dict, invoked_slugs: list[str]) -> str:
    traits = classifier.get("traits") or {}
    order = ["has_references", "has_phases", "has_hitl", "is_scheduled", "invokes_skills"]
    lines = []
    for key in order:
        fires = bool(traits.get(key, {}).get("fires", False))
        lines.append(f"{key}: {'true' if fires else 'false'}")
        if key == "invokes_skills" and fires and invoked_slugs:
            for slug in invoked_slugs:
                lines.append(f"  - /{slug}")
    return "\n".join(lines)


# --- BP path resolver ---


def resolve_bp_paths(
    sub_skill_name: str,
    patterns_root: Path,
    firing_traits: list[str] | None = None,
) -> list[str]:
    """Return the absolute BP paths for `sub_skill_name`, unioning the base
    list with any trait-gated conditional BPs whose trait is in
    `firing_traits`. Preserves declaration order (base first, then each
    conditional block in canonical trait order). Raises ValueError with the
    list of supported sub-skills if `sub_skill_name` is unknown — matches
    `build_pack`'s validation so direct callers get the same useful error."""
    if sub_skill_name not in _SUB_SKILL_BPS:
        raise ValueError(
            f"unsupported sub-skill: {sub_skill_name!r}. "
            f"supported: {sorted(_SUB_SKILL_BPS.keys())}"
        )
    filenames: list[str] = list(_SUB_SKILL_BPS[sub_skill_name])
    conditional = _SUB_SKILL_CONDITIONAL_BPS.get(sub_skill_name, {})
    if firing_traits:
        for trait in firing_traits:
            for fn in conditional.get(trait, []):
                if fn not in filenames:
                    filenames.append(fn)
    return [str(patterns_root / fn) for fn in filenames]


# --- References-list parser + pre-scaffold (Stage 9a) ---

# Matches a bullet line like:  - `scoping-questions.md` — full intake checklist.
# or:  - `frameworks-map.md` - per-problem framework map.
# Captures the filename (must end .md) and the purpose (after em-dash or hyphen-dash).
_REF_BULLET = re.compile(
    r"^\s*[-*]\s+`(?P<name>[a-z0-9][a-z0-9._-]*\.md)`\s*[—\-–]\s*(?P<purpose>.+?)\s*$",
    re.MULTILINE,
)


def parse_reference_exemplars(section_text: str | None) -> list[tuple[str, str]]:
    """Parse a "Reference exemplars" section body into [(filename, purpose), ...].
    Filenames must be backtick-wrapped and end in `.md`. Purpose follows an
    em-dash or hyphen-dash separator. Empty section or no matches → empty list."""
    if not section_text:
        return []
    matches = _REF_BULLET.findall(section_text)
    return [(name, purpose.strip()) for name, purpose in matches]


def prescaffold_references(
    spec_path: Path,
    target_skill_dir: Path,
    has_phases: bool = False,
) -> list[tuple[str, str]]:
    """Pre-scaffold the target skill dir from the spec's "Reference exemplars".

    Creates `target_skill_dir/references/<name>.md` (empty placeholder, single
    `# <stem>` header) for each entry, plus `target_skill_dir/SKILL.md` (stub
    with frontmatter + a `## References` section that contains one canonical
    `Read references/<name>.md for <purpose>.` line per entry).

    When `has_phases` is True, ALSO creates an empty `target_skill_dir/phases/`
    directory so `references_lint.py --has-phases` does not fail BP-009 on a
    missing `phases/` sibling. Stage 9b regression: caught by the omnibus
    5-trait E2E when `has_references ∧ has_phases` both fire.

    Returns the parsed reference list so callers can verify what was scaffolded.

    No-op (returns []) if the spec has no "Reference exemplars" section. The
    caller decides whether that is a BLOCKER (e.g., `has_references` fired but
    spec excerpt has no list) or simply skips pre-scaffolding (sub-skill is not
    being invoked)."""
    spec_text = spec_path.read_text(encoding="utf-8")
    sections = parse_spec_sections(spec_text)
    refs = parse_reference_exemplars(sections.get("Reference exemplars"))

    if not refs:
        return []

    refs_dir = target_skill_dir / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    for name, _purpose in refs:
        ref_path = refs_dir / name
        if not ref_path.exists():
            stem = ref_path.stem
            ref_path.write_text(f"# {stem}\n\nPlaceholder for spec entry `{name}`.\n", encoding="utf-8")

    # When the target skill is itself phased, BP-009 requires `phases/` and
    # `references/` as siblings. Create an empty placeholder so the
    # references_lint.py --has-phases walk doesn't fail on a missing dir.
    # The phase-designer sub-skill produces the actual procedure content
    # later; this is just structural scaffolding.
    if has_phases:
        phases_dir = target_skill_dir / "phases"
        phases_dir.mkdir(parents=True, exist_ok=True)

    # Strip trailing punctuation from the spec-supplied purpose so we can append
    # our own period without producing "first.." double-periods. (Spec entries
    # often end in '.' since they read as natural sentences.)
    citation_lines = "\n".join(
        f"- Read `references/{name}` for {purpose.rstrip('.!?').rstrip()}." for name, purpose in refs
    )
    skill_md = target_skill_dir / "SKILL.md"
    if not skill_md.exists():
        # Stub frontmatter (factory will overwrite via skill-frontmatter sub-skill;
        # this is just enough for the references-scaffolder lint to walk a valid file).
        skill_md.write_text(
            "---\n"
            "name: scaffolded-skill-stub\n"
            "description: Placeholder. Overwritten by skill-frontmatter Phase 3.\n"
            "---\n"
            "\n"
            "# scaffolded-skill-stub\n"
            "\n"
            "## References\n"
            f"{citation_lines}\n",
            encoding="utf-8",
        )

    return refs


# --- Main pack builder ---


def build_pack(
    spec_path: Path,
    classifier_path: Path,
    sub_skill_name: str,
    out_dir: Path,
    patterns_root: Path,
    target_skill_dir: Path | None = None,
) -> Path:
    if sub_skill_name not in _SUB_SKILL_BPS:
        raise ValueError(
            f"unsupported sub-skill: {sub_skill_name!r}. "
            f"supported: {sorted(_SUB_SKILL_BPS.keys())}"
        )

    spec_text = spec_path.read_text(encoding="utf-8")
    classifier = json.loads(classifier_path.read_text(encoding="utf-8"))
    sections = parse_spec_sections(spec_text)

    # Required sections for every spec (mirrors skill-spec-validator)
    for required in ("Company", "Skill slug", "One-line description", "Trigger phrases"):
        if required not in sections:
            raise ValueError(
                f"spec missing required section: '## {required}'. "
                f"Rerun /skill-spec-validator before Phase 3."
            )

    # Extract slug list for the traits block
    reuse_section = sections.get("Existing skills to reuse")
    invoked_slugs = extract_invoked_slugs(reuse_section)

    # Which traits fire? Used to union conditional BPs / sections.
    traits = classifier.get("traits", {}) or {}
    firing_traits = [
        name for name, verdict in traits.items()
        if isinstance(verdict, dict) and bool(verdict.get("fires", False))
    ]

    # Compose the spec excerpt — base sections plus any trait-gated additions.
    section_order: list[str] = list(_SUB_SKILL_SECTIONS[sub_skill_name])
    conditional_sections = _SUB_SKILL_CONDITIONAL_SECTIONS.get(sub_skill_name, {})
    for trait in firing_traits:
        for extra in conditional_sections.get(trait, []):
            if extra not in section_order:
                section_order.append(extra)

    excerpt_lines = []
    for section_name in section_order:
        body = sections.get(section_name)
        if body is None:
            # Optional sections are OK to omit; required already validated above
            continue
        excerpt_lines.append(f"### {section_name}")
        excerpt_lines.append(body)
        excerpt_lines.append("")
    spec_excerpt = "\n".join(excerpt_lines).rstrip()

    traits_block = render_traits_block(classifier, invoked_slugs)
    bp_paths = resolve_bp_paths(sub_skill_name, patterns_root, firing_traits)

    target_block = ""
    if target_skill_dir is not None:
        target_block = (
            "\n"
            "## Target skill directory\n"
            f"{target_skill_dir}\n"
        )

    pack = (
        f"# Input pack — {sub_skill_name}\n"
        "\n"
        "## Task\n"
        f"{_SUB_SKILL_TASK[sub_skill_name]}\n"
        "\n"
        "## Spec excerpt\n"
        "\n"
        f"{spec_excerpt}\n"
        "\n"
        "## Classified traits\n"
        "```\n"
        f"{traits_block}\n"
        "```\n"
        "\n"
        "## BPs to enforce\n"
        + "\n".join(f"- {p}" for p in bp_paths) + "\n"
        f"{target_block}"
        "\n"
        "## Output locations\n"
        f"{_SUB_SKILL_OUTPUT_BLURB[sub_skill_name]}\n"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    input_md = out_dir / "input.md"
    input_md.write_text(pack, encoding="utf-8")
    return input_md


# --- CLI ---


_DEFAULT_PATTERNS_ROOT = Path(__file__).resolve().parent.parent.parent / "patterns"


_USAGE = (
    "usage:\n"
    "  build_context_pack.py <spec-path> <classifier-json> <sub-skill-name> "
    "<out-dir> [--patterns-root <dir>] [--target-skill-dir <dir>]\n"
    "  build_context_pack.py --prescaffold-references <spec-path> <target-skill-dir>\n"
    "  build_context_pack.py --should-fire <sub-skill-name> <classifier-json>"
)


def _main(argv: list[str]) -> int:
    # --- Stage 9a: pre-scaffold mode (Stage 9b: + optional --has-phases) ---
    if len(argv) >= 2 and argv[1] == "--prescaffold-references":
        if len(argv) < 4:
            print(_USAGE, file=sys.stderr)
            return 2
        spec_path = Path(argv[2]).expanduser().resolve()
        target_skill_dir = Path(argv[3]).expanduser().resolve()
        has_phases = "--has-phases" in argv
        if not spec_path.is_file():
            print(f"error: spec not found: {spec_path}", file=sys.stderr)
            return 2
        refs = prescaffold_references(spec_path, target_skill_dir, has_phases=has_phases)
        print(json.dumps({"scaffolded": [name for name, _ in refs], "has_phases": has_phases}))
        return 0

    # --- Stage 9b: should-fire predicate mode ---
    # Exit 0 = sub-skill should fire. Exit 1 = sub-skill should NOT fire
    # (predicate returned False). Exit 2 = bad usage / unknown sub-skill / I/O.
    if len(argv) >= 2 and argv[1] == "--should-fire":
        if len(argv) < 4:
            print(_USAGE, file=sys.stderr)
            return 2
        sub_skill_name = argv[2]
        classifier_path = Path(argv[3]).expanduser().resolve()
        if not classifier_path.is_file():
            print(f"error: classifier json not found: {classifier_path}", file=sys.stderr)
            return 2
        try:
            classifier = json.loads(classifier_path.read_text(encoding="utf-8"))
            fires = should_fire(sub_skill_name, classifier)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(json.dumps({"sub_skill": sub_skill_name, "fires": fires}))
        return 0 if fires else 1

    # --- Default: pack-build mode ---
    if len(argv) < 5:
        print(_USAGE, file=sys.stderr)
        return 2

    spec_path = Path(argv[1]).expanduser().resolve()
    classifier_path = Path(argv[2]).expanduser().resolve()
    sub_skill_name = argv[3]
    out_dir = Path(argv[4]).expanduser().resolve()

    patterns_root = _DEFAULT_PATTERNS_ROOT
    if "--patterns-root" in argv:
        i = argv.index("--patterns-root")
        if i + 1 < len(argv):
            patterns_root = Path(argv[i + 1]).expanduser().resolve()

    target_skill_dir: Path | None = None
    if "--target-skill-dir" in argv:
        i = argv.index("--target-skill-dir")
        if i + 1 < len(argv):
            target_skill_dir = Path(argv[i + 1]).expanduser().resolve()

    if not spec_path.is_file():
        print(f"error: spec not found: {spec_path}", file=sys.stderr)
        return 2
    if not classifier_path.is_file():
        print(f"error: classifier json not found: {classifier_path}", file=sys.stderr)
        return 2

    try:
        result = build_pack(
            spec_path=spec_path,
            classifier_path=classifier_path,
            sub_skill_name=sub_skill_name,
            out_dir=out_dir,
            patterns_root=patterns_root,
            target_skill_dir=target_skill_dir,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(str(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
