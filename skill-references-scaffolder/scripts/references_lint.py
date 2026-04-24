#!/usr/bin/env python3
"""
references_lint.py — deterministic lint for a skill's references/ folder and
how its SKILL.md cites reference files, plus parallel-folder structure.

Implements the 3 rules in references/references-rules.md. Pure stdlib.

Usage:
    python3 references_lint.py <skill-dir-or-input.md> [--has-references] [--has-phases] [--two-level]
    python3 references_lint.py - --skill-dir <dir> [flags]   # read SKILL.md from stdin, inspect dir

Rule A (BP-008, universal when a `references/` folder exists):
    `references/` must be one level deep. No sub-directories.

Rule B (BP-007, only when --has-references):
    SKILL.md cites each `references/<file>.md` in the "Read references/X.md"
    form (or minor variants). Fails on uncited files. Fails on long
    inline content blocks (>=20 consecutive non-blank, non-heading lines
    that look like a table/list) that belong in a reference file.

Rule C (BP-009, only when --has-phases):
    The skill root must have `phases/` and `references/` at the same depth.
    By default nesting is a hard fail (`phases/<X>/references/...` or
    `references/<X>/phases/...`).
    When `--two-level` is ALSO set, `phases/<N>/references/` nesting is the
    canonical two-level director hierarchy (Stage 9 factory pattern) and is
    accepted; the lint emits an info line counting phase-scoped references/
    directories. Strict citation-walk enforcement (phase-scoped refs must be
    cited from exactly their phase director; cross-phase refs from SKILL.md
    or ≥2 phase directors) is deferred to Stage 9.0.6's strict-mode flip.
    Missing `assets/` emits a warn (not fail) — `assets/` is optional.

Exit codes:
    0 — lint passes
    1 — lint fails
    2 — bad usage / I/O error
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# "Read references/X.md ..." or "See references/X.md ..." or
# backtick-wrapped `references/X.md`, etc. The loose citation form:
# any textual reference to `references/<name>.md`. Filename character class
# accepts any non-whitespace, non-backtick, non-quote run so unicode
# filenames (e.g., `strategie-überblick.md`) are matched.
_CITATION_RE = re.compile(
    r"(?:^|[\s\(\[`'\"])references/([^\s`'\"()\[\]]+?\.md)",
    re.MULTILINE,
)

# Canonical BP-007 citation verb prefix. We warn if a reference is mentioned
# only in a non-canonical form (e.g., only in a bullet without a verb).
_CANONICAL_CITATION_RE = re.compile(
    r"\b(?:Read|See|Consult|Load|Use|Refer\s+to|per)\s+`?references/([^\s`'\"()\[\]]+?\.md)`?",
    re.IGNORECASE,
)

# Lines inside fenced code blocks are excluded from inline-content detection
# (we only care about SKILL.md prose).
_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)

# A "content-heavy line" looks like a table row, a list item that carries
# structured data, or a plain data/prose line >3 tokens. Blank lines and
# markdown headings break the streak.
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


@dataclass
class LintResult:
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.fails

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "fails": self.fails,
            "warns": self.warns,
            "info": self.info,
        }


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


def _find_references_dir(skill_dir: Path) -> Path | None:
    p = skill_dir / "references"
    return p if p.is_dir() else None


def _list_reference_files(ref_dir: Path) -> list[Path]:
    """Immediate-child .md files only (for Rule B citation checks)."""
    return sorted([p for p in ref_dir.iterdir() if p.is_file() and p.suffix == ".md"])


def _walk_references_for_nesting(ref_dir: Path) -> list[Path]:
    """Return any sub-directories under references/ (Rule A violations)."""
    subdirs: list[Path] = []
    for child in ref_dir.rglob("*"):
        # symlinked directories should also be flagged — they let an author
        # pretend to be flat while pointing at a nested tree.
        if child.is_dir():
            subdirs.append(child)
    return sorted(subdirs)


def _find_nested_parallel_violations(skill_dir: Path) -> list[str]:
    """Rule C: find any `phases/*/references` or `references/*/phases` paths."""
    hits: list[str] = []
    phases_dir = skill_dir / "phases"
    refs_dir = skill_dir / "references"
    if phases_dir.is_dir():
        for path in phases_dir.rglob("references"):
            if path.is_dir():
                hits.append(str(path.relative_to(skill_dir)))
    if refs_dir.is_dir():
        for path in refs_dir.rglob("phases"):
            if path.is_dir():
                hits.append(str(path.relative_to(skill_dir)))
    return sorted(set(hits))


def _detect_inline_content_blocks(skill_md_text: str) -> list[tuple[int, int]]:
    """Return (start_line, end_line) spans of inline content that looks like
    it belongs in a reference file. A span is:
      - >= 20 consecutive non-blank, non-heading lines, OR
      - >= 10 consecutive table rows (pipe-delimited).
    Fenced code blocks are stripped before scanning."""
    stripped = _strip_code_fences(skill_md_text)
    lines = stripped.splitlines()
    spans: list[tuple[int, int]] = []

    # Pass 1: long table spans (>=10 rows)
    run_start = -1
    run_len = 0
    for i, ln in enumerate(lines):
        if _TABLE_ROW_RE.match(ln):
            if run_start < 0:
                run_start = i
            run_len += 1
        else:
            if run_len >= 10:
                spans.append((run_start, i - 1))
            run_start = -1
            run_len = 0
    if run_len >= 10:
        spans.append((run_start, len(lines) - 1))

    # Pass 2: long dense-prose/list spans (>=20 lines that are non-blank, non-heading)
    run_start = -1
    run_len = 0
    for i, ln in enumerate(lines):
        is_dense = bool(ln.strip()) and not _HEADING_RE.match(ln)
        if is_dense:
            if run_start < 0:
                run_start = i
            run_len += 1
        else:
            if run_len >= 20:
                spans.append((run_start, i - 1))
            run_start = -1
            run_len = 0
    if run_len >= 20:
        spans.append((run_start, len(lines) - 1))

    # Deduplicate overlapping spans (prefer the larger one).
    spans.sort()
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _citations_in(text: str) -> set[str]:
    return {m.group(1) for m in _CITATION_RE.finditer(text)}


def _canonical_citations_in(text: str) -> set[str]:
    return {m.group(1) for m in _CANONICAL_CITATION_RE.finditer(text)}


def lint_paths(
    skill_dir: Path,
    skill_md_text: str | None = None,
    has_references: bool = False,
    has_phases: bool = False,
    two_level: bool = False,
) -> LintResult:
    result = LintResult()

    if not skill_dir.is_dir():
        result.fails.append(f"skill directory not found: {skill_dir}")
        return result

    # Resolve SKILL.md text
    skill_md_path = skill_dir / "SKILL.md"
    if skill_md_text is None:
        if skill_md_path.is_file():
            try:
                skill_md_text = skill_md_path.read_text(encoding="utf-8")
            except OSError as exc:
                result.fails.append(f"could not read SKILL.md: {exc}")
                return result
        else:
            skill_md_text = ""

    ref_dir = _find_references_dir(skill_dir)

    # ------------------------------------------------------------------
    # Rule A — BP-008 (universal if references/ exists)
    # ------------------------------------------------------------------
    if ref_dir is not None:
        subdirs = _walk_references_for_nesting(ref_dir)
        if subdirs:
            rels = sorted(str(p.relative_to(skill_dir)) for p in subdirs)
            result.fails.append(
                f"BP-008: references/ must be one level deep; found "
                f"sub-director{'y' if len(rels) == 1 else 'ies'}: {rels}"
            )
        else:
            ref_files = _list_reference_files(ref_dir)
            result.info.append(
                f"references/ is flat with {len(ref_files)} .md file(s)"
            )
    else:
        result.info.append("no references/ directory present")

    # ------------------------------------------------------------------
    # Rule B — BP-007 (only when --has-references)
    # ------------------------------------------------------------------
    if has_references:
        if ref_dir is None:
            result.fails.append(
                "BP-007: --has-references set but no references/ directory "
                "found in skill root"
            )
        else:
            ref_files = _list_reference_files(ref_dir)
            if not ref_files:
                result.warns.append(
                    "BP-007: references/ exists but is empty; "
                    "--has-references was set"
                )
            canonical = _canonical_citations_in(skill_md_text)
            loose = _citations_in(skill_md_text)
            uncited: list[str] = []
            non_canonical: list[str] = []
            for rf in ref_files:
                name = rf.name
                if name in canonical:
                    continue
                if name in loose:
                    non_canonical.append(name)
                    continue
                uncited.append(name)
            if uncited:
                result.fails.append(
                    f"BP-007: reference file(s) not cited in SKILL.md: "
                    f"{sorted(uncited)}. Use 'Read references/<name>.md for "
                    f"<purpose>' phrasing."
                )
            if non_canonical:
                result.warns.append(
                    f"BP-007: reference file(s) cited but without a canonical "
                    f"verb (Read/See/Consult/Load/Use/Refer to/per): "
                    f"{sorted(non_canonical)}"
                )

            # Inline-content detection: long tables or dense blocks in
            # SKILL.md that belong in references/.
            spans = _detect_inline_content_blocks(skill_md_text)
            if spans:
                preview = [
                    f"lines {s + 1}-{e + 1} ({e - s + 1} lines)"
                    for s, e in spans
                ]
                result.fails.append(
                    f"BP-007: SKILL.md contains inline block(s) that belong in "
                    f"references/: {preview}. Move to references/<topic>.md "
                    f"and cite with 'Read references/<topic>.md for <purpose>'."
                )

    # ------------------------------------------------------------------
    # Rule C — BP-009 (only when --has-phases)
    # ------------------------------------------------------------------
    if has_phases:
        phases_dir = skill_dir / "phases"
        if not phases_dir.is_dir():
            result.fails.append(
                "BP-009: --has-phases set but no phases/ directory found in "
                "skill root"
            )
        if ref_dir is None:
            result.fails.append(
                "BP-009: --has-phases set but no references/ directory found "
                "in skill root; parallel-folder pattern requires both"
            )
        nested = _find_nested_parallel_violations(skill_dir)
        if nested:
            if two_level:
                # In two-level-hierarchy mode (Stage 9.0.4+), `phases/<N>/references/`
                # nesting is the canonical director-scoped reference location, not a
                # violation. We surface it as an info line so the operator can see
                # which phase-dirs carry scoped refs. `references/<X>/phases/` is
                # still nonsensical and NOT covered by two-level mode — partition
                # the nested list.
                scoped = [n for n in nested if n.startswith("phases/")]
                reversed_nest = [n for n in nested if not n.startswith("phases/")]
                if scoped:
                    result.info.append(
                        f"two-level hierarchy detected: "
                        f"{len(scoped)} phase-scoped references/ dir(s) at {scoped}"
                    )
                if reversed_nest:
                    result.fails.append(
                        f"BP-009: nested parallel folder(s) found: {reversed_nest}. "
                        f"phases/ and references/ must be siblings at the skill root."
                    )
            else:
                result.fails.append(
                    f"BP-009: nested parallel folder(s) found: {nested}. "
                    f"phases/ and references/ must be siblings at the skill root."
                )
        assets_dir = skill_dir / "assets"
        if not assets_dir.is_dir():
            result.warns.append(
                "BP-009: no assets/ directory at skill root; assets/ is "
                "optional — ignore this warning if the skill has no templates "
                "or static files"
            )
        else:
            result.info.append("assets/ directory present at skill root")

    return result


def _resolve_target(arg: str) -> tuple[Path, str | None]:
    """Accept either a skill directory or a path to an input.md.

    If an input.md is given, the parent directory is treated as the skill
    directory and SKILL.md text is read from disk.
    """
    p = Path(arg).expanduser().resolve()
    if p.is_dir():
        return p, None
    if p.is_file():
        # If a SKILL.md is passed, treat its parent as the skill dir.
        if p.name == "SKILL.md":
            return p.parent, p.read_text(encoding="utf-8")
        # Otherwise treat as an input.md fixture — parent directory.
        return p.parent, None
    raise FileNotFoundError(f"target not found: {p}")


def _main(argv: list[str]) -> int:
    args = argv[1:]
    if not args:
        print(
            "usage: references_lint.py <skill-dir-or-SKILL.md> "
            "[--has-references] [--has-phases] [--two-level]",
            file=sys.stderr,
        )
        return 2
    target = args[0]
    has_references = "--has-references" in args[1:]
    has_phases = "--has-phases" in args[1:]
    two_level = "--two-level" in args[1:]
    try:
        skill_dir, override_text = _resolve_target(target)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = lint_paths(
        skill_dir,
        skill_md_text=override_text,
        has_references=has_references,
        has_phases=has_phases,
        two_level=two_level,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
