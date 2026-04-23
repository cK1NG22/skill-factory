#!/usr/bin/env python3
"""
build_context_pack.py — Phase 3 of the Skill Factory.

Takes a validated client spec and the Phase 2 classifier JSON output and
materializes `input.md` in the exact shape a sub-skill expects. This script
is the lone bridge between the driver's classifier and any sub-skill's
isolated Agent subtask — per BP-033, sub-skills read ONLY their `input.md`.

Usage:
    build_context_pack.py <spec-path> <classifier-json> <sub-skill-name> <out-dir>

Currently supported <sub-skill-name> values:
    skill-frontmatter

Output:
    <out-dir>/input.md — the materialized context pack.

Exit codes:
    0 — pack materialized successfully
    1 — spec missing a required section or sub-skill name unsupported
    2 — usage / I/O error
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# --- Universal + Conditional BP lookup per sub-skill ---
# For Stage 6b, only `skill-frontmatter` is wired. Each sub-skill has its own
# canonical list of BPs — the frontmatter sub-skill uses the 5 frontmatter
# Universals (BP-001..BP-005). Later sub-skills will add their own lists; the
# trait-gated Conditional BPs (BP-007, BP-009, etc.) are carried in packs for
# OTHER sub-skills (phase-designer, references-scaffolder, etc.), not here.
_SUB_SKILL_BPS: dict[str, list[str]] = {
    "skill-frontmatter": [
        "bp-001-trigger-phrases.md",
        "bp-002-pushy-description.md",
        "bp-003-name-rules.md",
        "bp-004-description-length.md",
        "bp-005-allowed-tools.md",
    ],
}

# --- Sections each sub-skill needs from the spec ---
# Keeping packs narrow keeps sub-skill reasoning honest — don't ship sections
# the sub-skill does not use.
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
}

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
}

# --- Task lines per sub-skill ---
_SUB_SKILL_TASK: dict[str, str] = {
    "skill-frontmatter": (
        "Generate compliant YAML frontmatter for a factory-authored skill. "
        "Write `output.yaml`, `output.md`, and `notes.md` into the same directory as this `input.md`."
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
    traits = classifier.get("traits", {})
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


def resolve_bp_paths(sub_skill_name: str, patterns_root: Path) -> list[str]:
    filenames = _SUB_SKILL_BPS[sub_skill_name]
    return [str(patterns_root / fn) for fn in filenames]


# --- Main pack builder ---


def build_pack(
    spec_path: Path,
    classifier_path: Path,
    sub_skill_name: str,
    out_dir: Path,
    patterns_root: Path,
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

    # Compose the spec excerpt
    excerpt_lines = []
    for section_name in _SUB_SKILL_SECTIONS[sub_skill_name]:
        body = sections.get(section_name)
        if body is None:
            # Optional sections are OK to omit; required already validated above
            continue
        excerpt_lines.append(f"### {section_name}")
        excerpt_lines.append(body)
        excerpt_lines.append("")
    spec_excerpt = "\n".join(excerpt_lines).rstrip()

    traits_block = render_traits_block(classifier, invoked_slugs)
    bp_paths = resolve_bp_paths(sub_skill_name, patterns_root)

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


def _main(argv: list[str]) -> int:
    if len(argv) < 5:
        print(
            "usage: build_context_pack.py <spec-path> <classifier-json> "
            "<sub-skill-name> <out-dir> [--patterns-root <dir>]",
            file=sys.stderr,
        )
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
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(str(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
