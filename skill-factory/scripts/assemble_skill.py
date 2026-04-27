#!/usr/bin/env python3
"""
assemble_skill.py — Phase 8a of the Skill Factory.

Reads the per-phase outputs scattered under <work>/phases/NN-*/ and assembles
them into a single skill directory at <work>/assembled/<slug>/. The gate
(Phase 8b, skill-compliance-gate) then verifies what this script produces.

Phase output → assembled file map (always-fires phases first):

  03-skill-frontmatter/output.yaml      → top of <slug>/SKILL.md (frontmatter)
  03-skill-frontmatter/input.md         → spec excerpt mined for body sections
                                           (One-line description, walkthrough)

Conditional, gated by classifier traits:

  04-skill-phase-designer/output.md     → ## Procedure section of SKILL.md
                                           (when has_phases.fires)
  05-skill-references-scaffolder/<dir>  → references/ tree + phases/ scaffold
                                           (when has_references.fires)
  06-skill-cron-observability/...       → scripts/instrumentation_snippet.py
                                           (when is_scheduled.fires)
  07-skill-signed-handoff/...           → scripts/<slug>_signature.py
                                           (when has_phases ∧ invokes_skills)

Manifest:

  <work>/assembled/<slug>/ASSEMBLY-MANIFEST.json — records which phase output
  contributed to which file in the assembled tree. Useful for debug + the
  Stage 10c self-bootstrap diff (regenerated tree should match committed
  state byte-for-byte except for known meta-skill divergences).

Exit codes:
  0 — success.
  1 — missing required phase output (assembly cannot proceed).
  2 — malformed phase output (e.g. frontmatter lacks closing `---`).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\Aname:\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)
_SLUG_FROM_INPUT_RE = re.compile(
    r"^###\s+Skill slug\s*\n+([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE
)


@dataclass
class AssemblyResult:
    """Result of an assemble_skill run.

    `assembled_dir` is the path to the assembled skill directory. `manifest`
    is the dict written to ASSEMBLY-MANIFEST.json. `notes` is a list of
    informational strings appended in declaration order.
    """

    assembled_dir: Path
    manifest: dict
    notes: list[str] = field(default_factory=list)


class AssemblyError(Exception):
    """Raised on missing/malformed phase outputs. Carries an exit-code hint
    via the `code` attribute (1 = missing, 2 = malformed). The CLI maps this
    back to process exit codes."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def _read_classifier(work_dir: Path) -> dict:
    classifier_path = work_dir / "classifier.json"
    if not classifier_path.is_file():
        raise AssemblyError(
            f"classifier.json missing at {classifier_path}", code=1
        )
    try:
        return json.loads(classifier_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssemblyError(
            f"classifier.json malformed — {exc}", code=2
        ) from exc


def _firing_traits(classifier: dict) -> set[str]:
    traits = classifier.get("traits") or {}
    return {
        name for name, verdict in traits.items()
        if isinstance(verdict, dict) and bool(verdict.get("fires", False))
    }


def _read_frontmatter_yaml(work_dir: Path) -> str:
    """Phase 3's output.yaml is the YAML between `---` delimiters (the raw
    frontmatter block, parseable). Returns the YAML body without delimiters."""
    yaml_path = work_dir / "phases" / "03-skill-frontmatter" / "output.yaml"
    if not yaml_path.is_file():
        raise AssemblyError(
            f"required phase output missing: {yaml_path}", code=1
        )
    body = yaml_path.read_text(encoding="utf-8").strip()
    if body.startswith("---"):
        body = body[3:].lstrip("\n")
    if body.endswith("---"):
        body = body[: -3].rstrip("\n")
    if not body.strip():
        raise AssemblyError(
            f"frontmatter output.yaml empty at {yaml_path}", code=2
        )
    return body.strip()


def _extract_slug(yaml_body: str, work_dir: Path) -> str:
    """Slug comes from the frontmatter `name:` field. Falls back to the spec
    excerpt's `### Skill slug` block if frontmatter parsing fails — tests use
    that fallback when constructing minimal fixtures."""
    m = _FRONTMATTER_RE.search(yaml_body)
    if m:
        return m.group(1)
    input_md = work_dir / "phases" / "03-skill-frontmatter" / "input.md"
    if input_md.is_file():
        m2 = _SLUG_FROM_INPUT_RE.search(input_md.read_text(encoding="utf-8"))
        if m2:
            return m2.group(1)
    raise AssemblyError(
        "could not determine skill slug from frontmatter or spec excerpt",
        code=2,
    )


def _read_procedure(work_dir: Path) -> str:
    """Phase 4's output.md is the `## Procedure` section ready to paste."""
    md_path = work_dir / "phases" / "04-skill-phase-designer" / "output.md"
    if not md_path.is_file():
        raise AssemblyError(
            f"required phase output missing (has_phases fired): {md_path}",
            code=1,
        )
    body = md_path.read_text(encoding="utf-8").strip()
    if not body:
        raise AssemblyError(
            f"phase-designer output.md empty at {md_path}", code=2
        )
    if not body.lstrip().startswith("## Procedure"):
        body = "## Procedure\n\n" + body
    return body


def _spec_section(work_dir: Path, h3_name: str) -> str | None:
    """Pull a single H3 block out of Phase 3's input.md (the spec excerpt
    block). Returns the body text without the heading, or None if absent."""
    input_md = work_dir / "phases" / "03-skill-frontmatter" / "input.md"
    if not input_md.is_file():
        return None
    text = input_md.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^###\s+{re.escape(h3_name)}\s*\n(?P<body>.*?)(?=^###\s|^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None
    return m.group("body").strip() or None


def _copy_references(work_dir: Path, assembled: Path,
                     manifest: dict) -> None:
    """Phase 5's pre-scaffolded target dir lives at
    <work>/phases/05-skill-references-scaffolder/target/. Copy its
    references/ + (optional) phases/ tree into the assembled dir."""
    target = work_dir / "phases" / "05-skill-references-scaffolder" / "target"
    src_refs = target / "references"
    if not src_refs.is_dir():
        return
    dst_refs = assembled / "references"
    dst_refs.mkdir(parents=True, exist_ok=True)
    for entry in sorted(src_refs.iterdir()):
        if entry.is_file():
            dst = dst_refs / entry.name
            shutil.copy2(entry, dst)
            manifest.setdefault("references", []).append(entry.name)


def _scaffold_phases_dir(assembled: Path) -> None:
    (assembled / "phases").mkdir(parents=True, exist_ok=True)


def _copy_cron_snippet(work_dir: Path, assembled: Path,
                       manifest: dict) -> None:
    """Phase 6 writes `instrumentation-snippet.md` (a fenced Python block).
    We extract the code and write it as `scripts/instrumentation_snippet.py`
    in the assembled tree. Stage 10b keeps this conservative — extracting
    the block rather than copying the markdown so the assembled skill ships
    runnable Python only."""
    snippet_md = (
        work_dir / "phases" / "06-skill-cron-observability"
        / "instrumentation-snippet.md"
    )
    if not snippet_md.is_file():
        return
    text = snippet_md.read_text(encoding="utf-8")
    fence = re.search(
        r"```python\n(?P<body>.*?)\n```",
        text, re.DOTALL,
    )
    if not fence:
        # Fall back: copy the .md verbatim so a human can resolve it. Don't
        # raise — cron output is a soft-fail per BP-029 incremental shipping.
        dst = assembled / "scripts" / "instrumentation-snippet.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snippet_md, dst)
        manifest.setdefault("scripts", []).append(
            "instrumentation-snippet.md"
        )
        return
    dst = assembled / "scripts" / "instrumentation_snippet.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(fence.group("body") + "\n", encoding="utf-8")
    manifest.setdefault("scripts", []).append("instrumentation_snippet.py")


def _copy_signature_script(work_dir: Path, assembled: Path,
                           slug: str, manifest: dict) -> None:
    """Phase 7 emits `output-signature-template.py`. The assembled skill
    receives it as `scripts/<slug>_signature.py` per BP-024 contract."""
    src = (
        work_dir / "phases" / "07-skill-signed-handoff"
        / "output-signature-template.py"
    )
    if not src.is_file():
        return
    dst = assembled / "scripts" / f"{slug}_signature.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    manifest.setdefault("scripts", []).append(f"{slug}_signature.py")


def _compose_skill_md(yaml_body: str, slug: str, description: str | None,
                      walkthrough: str | None,
                      procedure: str | None) -> str:
    """Compose the assembled SKILL.md. Frontmatter on top, H1 (slug),
    a short body intro, and (optionally) the Procedure section. Keep this
    minimal — the gate's body-size check tolerates thin directors."""
    parts: list[str] = []
    parts.append("---")
    parts.append(yaml_body)
    parts.append("---")
    parts.append("")
    parts.append(f"# {slug}")
    parts.append("")
    if description:
        parts.append(description.strip())
        parts.append("")
    if walkthrough:
        parts.append("## Happy-path walkthrough")
        parts.append("")
        parts.append(walkthrough.strip())
        parts.append("")
    if procedure:
        parts.append(procedure.strip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def assemble(work_dir: Path) -> AssemblyResult:
    """Assemble the per-phase outputs at <work>/phases/ into a single skill
    directory at <work>/assembled/<slug>/. Returns an AssemblyResult; raises
    AssemblyError on missing/malformed inputs."""
    work_dir = work_dir.resolve()
    classifier = _read_classifier(work_dir)
    firing = _firing_traits(classifier)

    yaml_body = _read_frontmatter_yaml(work_dir)
    slug = _extract_slug(yaml_body, work_dir)

    description = _spec_section(work_dir, "One-line description")
    walkthrough = _spec_section(work_dir, "Happy-path walkthrough")

    procedure = None
    if "has_phases" in firing:
        procedure = _read_procedure(work_dir)

    assembled = work_dir / "assembled" / slug
    if assembled.exists():
        shutil.rmtree(assembled)
    assembled.mkdir(parents=True)

    skill_md = _compose_skill_md(
        yaml_body=yaml_body, slug=slug, description=description,
        walkthrough=walkthrough, procedure=procedure,
    )
    (assembled / "SKILL.md").write_text(skill_md, encoding="utf-8")

    manifest: dict = {
        "slug": slug,
        "firing_traits": sorted(firing),
        "skill_md": "SKILL.md",
        "from_phases": {
            "03-skill-frontmatter": ["output.yaml"],
        },
    }
    if procedure is not None:
        manifest["from_phases"]["04-skill-phase-designer"] = ["output.md"]

    if "has_references" in firing:
        _copy_references(work_dir, assembled, manifest)
    if "has_phases" in firing:
        _scaffold_phases_dir(assembled)
    if "is_scheduled" in firing:
        _copy_cron_snippet(work_dir, assembled, manifest)
    if "has_phases" in firing and "invokes_skills" in firing:
        _copy_signature_script(work_dir, assembled, slug, manifest)

    manifest_path = assembled / "ASSEMBLY-MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return AssemblyResult(assembled_dir=assembled, manifest=manifest)


_USAGE = "usage: assemble_skill.py <work-dir>"


def _main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(_USAGE, file=sys.stderr)
        return 2
    work_dir = Path(argv[1]).expanduser().resolve()
    if not work_dir.is_dir():
        print(f"error: work-dir not found: {work_dir}", file=sys.stderr)
        return 2
    try:
        result = assemble(work_dir)
    except AssemblyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code
    print(str(result.assembled_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
