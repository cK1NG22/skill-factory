#!/usr/bin/env python3
"""
trait_predicates.py — the Skill Factory's Phase 2 classifier.

Evaluates 5 binary trait predicates against either a client spec (authoring mode)
or an existing skill directory (dogfood / classification mode). Output drives
which Conditional BP sub-skills the driver unions into the Phase 4 build.

The 5 traits (locked by ADR-0001):
    has_references   — skill will produce framework/lookup content
    has_phases       — skill executes a workflow of >=3 distinct steps
    has_hitl         — skill declares user gates mid-flow
    is_scheduled     — skill has a scheduling section (cron, recurring)
    invokes_skills   — skill composes with another ecosystem skill via Agent

Edge cases handled (per feedback-trait-classifier-edge-cases.md):
    1. sibling .md files at skill root count as has_references
    2. alternate phase naming ("## Workflow", "## 1. Foo") counts as has_phases
    3. gstack-style bash preamble is skipped before scanning invokes_skills
    4. paired-family toggles (/freeze ↔ /unfreeze) do NOT count as invokes_skills

Usage (CLI):
    python3 trait_predicates.py spec <path-to-client-spec.md>
    python3 trait_predicates.py skill <path-to-skill-dir>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

DEFAULT_ECOSYSTEM = Path.home() / ".claude" / "skills"


class Verdict(NamedTuple):
    fires: bool
    evidence: str


# ---------- helpers ----------


def _strip_gstack_preamble(text: str) -> str:
    """
    Edge case 3: some ecosystem skills (gstack family) open with 50+ lines of
    bash that include paths like `~/.claude/skills/gstack/bin/<tool>` that
    naive /<skill> regex would false-match. Skip content before the first
    Markdown H2 (that is NOT inside a fenced code block) if any bash preamble
    sentinels appear above it.
    """
    lines = text.splitlines()
    preamble_sentinels = re.compile(
        r"""^(
            _[A-Z_]+=          # _FOO=...
            | source\s          # source <path>
            | eval\s"           # eval "..."
            | if\s\[\s"\$_      # if [ "$_...
            | export\s[A-Z_]+=  # export FOO=...
        )""",
        re.VERBOSE,
    )
    in_code_fence = False
    first_h2 = None
    saw_preamble = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            if preamble_sentinels.match(line):
                saw_preamble = True
            continue
        if preamble_sentinels.match(line):
            saw_preamble = True
            continue
        if re.match(r"^#{1,3}\s", line) and first_h2 is None:
            first_h2 = i
            break
    if saw_preamble and first_h2 is not None:
        return "\n".join(lines[first_h2:])
    return text


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4 :].lstrip("\n")


def _read_skill_text(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")
    return skill_md.read_text(encoding="utf-8")


# ---------- has_references ----------


def has_references_skill(skill_dir: Path) -> Verdict:
    """Dogfood / classification mode."""
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir() and any(ref_dir.glob("*.md")):
        count = len(list(ref_dir.glob("*.md")))
        return Verdict(True, f"references/ directory contains {count} .md file(s)")

    # Edge case 1: sibling .md files at skill root count as has_references
    sibling_mds = [
        p for p in skill_dir.glob("*.md") if p.name.upper() != "SKILL.MD"
    ]
    if sibling_mds:
        names = ", ".join(sorted(p.name for p in sibling_mds))
        return Verdict(True, f"sibling .md files at skill root: {names}")

    # Inline-body proxy: >=200 lines of body content after frontmatter is a signal
    try:
        body = _strip_frontmatter(_read_skill_text(skill_dir))
        if len([ln for ln in body.splitlines() if ln.strip()]) >= 200:
            return Verdict(True, "SKILL.md body has >=200 non-empty lines (inline reference content)")
    except FileNotFoundError:
        pass

    return Verdict(False, "no references/ dir, no sibling .md, SKILL.md body <200 lines")


def has_references_spec(spec_text: str) -> Verdict:
    """Authoring mode — infer from spec content."""
    body = _strip_frontmatter(spec_text).lower()
    signals = [
        "reference file",
        "lookup table",
        "framework",
        "rubric",
        "schema definition",
        "knowledge base",
        "methodology",
        "best-practice catalog",
    ]
    hits = [s for s in signals if s in body]
    if hits:
        return Verdict(True, f"spec mentions reference-content signals: {hits}")
    return Verdict(False, "no reference-content signals in spec body")


# ---------- has_phases ----------


_PHASE_HEADING = re.compile(r"^#{2,4}\s+(?:Phase|Step)\s+\d+", re.MULTILINE)
_NUMBERED_HEADING = re.compile(r"^#{2,4}\s+\d+[\.\)]\s+\S", re.MULTILINE)
_WORKFLOW_HEADING = re.compile(
    r"^##\s+(?:Workflow|Procedure|Process)\b", re.MULTILINE | re.IGNORECASE
)
_NUMBERED_LIST_ITEM = re.compile(r"^\s*\d+[\.\)]\s+\S", re.MULTILINE)


def _count_numbered_list_items(block: str) -> int:
    return len(_NUMBERED_LIST_ITEM.findall(block))


def has_phases_any(text: str) -> Verdict:
    phase_count = len(_PHASE_HEADING.findall(text))
    if phase_count >= 3:
        return Verdict(True, f"{phase_count} 'Phase N' / 'Step N' headings")

    numbered_count = len(_NUMBERED_HEADING.findall(text))
    if numbered_count >= 3:
        return Verdict(True, f"{numbered_count} numbered section headings (e.g., '## 1. Foo')")

    # Edge case 2: "## Workflow" with >=3 numbered list items in first 50 lines
    match = _WORKFLOW_HEADING.search(text)
    if match:
        start = match.end()
        lines = text[start:].splitlines()[:50]
        block = "\n".join(lines)
        count = _count_numbered_list_items(block)
        if count >= 3:
            return Verdict(True, f"'## Workflow' (or Procedure/Process) section with {count} numbered list items")

    # Happy-path walkthrough with >=3 numbered list items counts as phased
    hp_match = re.search(
        r"^#{1,4}\s+(?:Happy[-\s]path|Walkthrough)",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    if hp_match:
        start = hp_match.end()
        next_heading = re.search(r"^#{1,4}\s", text[start:], re.MULTILINE)
        end = start + (next_heading.start() if next_heading else len(text) - start)
        count = _count_numbered_list_items(text[start:end])
        if count >= 3:
            return Verdict(True, f"Happy-path walkthrough has {count} numbered steps")

    return Verdict(False, "<3 phase headings, <3 numbered headings, no Workflow section with 3+ items")


# ---------- has_hitl ----------


_HITL_SIGNALS = [
    r"AskUserQuestion",
    r"\bask the user\b",
    r"\bprompt the user\b",
    r"\bwait for (?:the )?user\b",
    r"\buser confirm(?:s|ation|ed)?\b",
    r"\b(?:hard )?gate\b",
    r"\bstop and (?:review|ask|confirm)\b",
    r"\buser (?:chooses|decides|selects)\b",
    r"\bbefore proceeding\b",
]


def has_hitl_any(text: str) -> Verdict:
    # Apply preamble strip (edge case 3 also matters for HITL — bash preamble
    # may contain unreachable AskUserQuestion calls in dead branches)
    scanned = _strip_gstack_preamble(text)
    hits = []
    for pat in _HITL_SIGNALS:
        matches = re.findall(pat, scanned, re.IGNORECASE)
        if matches:
            hits.append(f"{pat!r}x{len(matches)}")
    # Fire if any strong signal (AskUserQuestion) OR >=2 weaker signals
    if re.search(r"AskUserQuestion", scanned):
        return Verdict(True, f"AskUserQuestion usage present; signals={hits}")
    # count distinct weaker patterns
    if len(hits) >= 2:
        return Verdict(True, f"multiple HITL signals: {hits}")
    return Verdict(False, f"insufficient HITL signals (found {hits})")


# ---------- is_scheduled ----------


_SCHED_SIGNALS = re.compile(
    r"""\b(
        cron
        | crontab
        | scheduled
        | schedule:
        | daily
        | weekly
        | hourly
        | nightly
        | recurring
        | every\s+\d+\s+(?:minute|hour|day|week)s?
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)


def is_scheduled_any(text: str) -> Verdict:
    matches = _SCHED_SIGNALS.findall(text)
    if matches:
        distinct = sorted({m.lower() for m in matches})
        return Verdict(True, f"scheduling keywords: {distinct}")
    return Verdict(False, "no scheduling keywords")


# ---------- invokes_skills ----------


_SLASH_SKILL = re.compile(r"(?<![a-zA-Z0-9_/])/([a-z][a-z0-9-]{1,63})\b")
_REUSE_SECTION = re.compile(
    r"^#{1,4}\s+(?:Existing\s+skills(?:\s+to\s+reuse)?|Reuse|Invokes)",
    re.MULTILINE | re.IGNORECASE,
)
_PAIRED_FAMILY_BLOCKLIST = {
    # skills whose /<name> mentions elsewhere are companion commands, not Agent invocations
    "unfreeze",
    "freeze",
    "careful",
    "guard",
    "unlock",
}


def _extract_reuse_block(text: str) -> str | None:
    m = _REUSE_SECTION.search(text)
    if not m:
        return None
    start = m.end()
    next_heading = re.search(r"^#{1,4}\s", text[start:], re.MULTILINE)
    end = start + (next_heading.start() if next_heading else len(text) - start)
    return text[start:end]


def invokes_skills_spec(
    spec_text: str, self_slug: str | None = None, ecosystem: Path = DEFAULT_ECOSYSTEM
) -> Verdict:
    """
    Authoring mode: spec's 'Existing skills to reuse' section is the ONLY signal.
    Per BP-034, sub-skill invocation is justified only by explicit declaration.
    Ecosystem existence check mirrors the spec-validator's BP-034 gate.
    """
    block = _extract_reuse_block(spec_text)
    if block is None:
        return Verdict(False, "no 'Existing skills to reuse' section")
    if re.search(r"^\s*none\s*$", block.strip(), re.IGNORECASE | re.MULTILINE):
        return Verdict(False, "reuse section declares 'None'")
    named = set(_SLASH_SKILL.findall(block))
    if self_slug:
        named.discard(self_slug)
    existing = sorted(n for n in named if (ecosystem / n).is_dir())
    if existing:
        return Verdict(True, f"invokes existing skill(s): {existing}")
    if named:
        return Verdict(False, f"names {sorted(named)} but none exist under {ecosystem}")
    return Verdict(False, "reuse section present but lists no /<skill> entries")


def invokes_skills_skill(
    skill_dir: Path, ecosystem: Path = DEFAULT_ECOSYSTEM
) -> Verdict:
    """
    Dogfood mode: scan SKILL.md body for /<skill> mentions. Apply edge case 3
    (strip gstack preamble) and edge case 4 (paired-family exclusion).
    """
    text = _read_skill_text(skill_dir)
    self_slug = skill_dir.name.lower()
    stripped = _strip_gstack_preamble(_strip_frontmatter(text))

    # Also drop inline code spans that look like file paths
    stripped = re.sub(r"`[^`\n]*[/~][^`\n]*`", "``", stripped)
    # Drop fenced code blocks entirely — real invocations are in prose
    stripped = re.sub(r"```[\s\S]*?```", "", stripped)

    candidates = set(_SLASH_SKILL.findall(stripped))
    candidates.discard(self_slug)

    # Edge case 4: paired-family toggles don't count as invocations
    paired_hits = candidates & _PAIRED_FAMILY_BLOCKLIST
    candidates -= _PAIRED_FAMILY_BLOCKLIST

    # Exclude anything that doesn't exist in the ecosystem (false positives)
    existing = sorted(c for c in candidates if (ecosystem / c).is_dir())

    if existing:
        note = f"invokes existing skill(s): {existing}"
        if paired_hits:
            note += f" (paired-family mentions ignored: {sorted(paired_hits)})"
        return Verdict(True, note)
    if paired_hits:
        return Verdict(False, f"only paired-family mentions ({sorted(paired_hits)}) — excluded per edge case 4")
    return Verdict(False, "no /<skill> references to existing ecosystem skills")


# ---------- classifier entry points ----------


def classify_spec(
    spec_path: Path, ecosystem: Path = DEFAULT_ECOSYSTEM
) -> dict:
    text = spec_path.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)
    return {
        "mode": "spec",
        "input": str(spec_path),
        "traits": {
            "has_references": _verdict_to_dict(has_references_spec(body)),
            "has_phases": _verdict_to_dict(has_phases_any(body)),
            "has_hitl": _verdict_to_dict(has_hitl_any(body)),
            "is_scheduled": _verdict_to_dict(is_scheduled_any(body)),
            "invokes_skills": _verdict_to_dict(
                invokes_skills_spec(body, ecosystem=ecosystem)
            ),
        },
    }


def classify_skill(
    skill_dir: Path, ecosystem: Path = DEFAULT_ECOSYSTEM
) -> dict:
    # Pass full text (including frontmatter) to keyword-scanning predicates.
    # Real skills put scheduling hints and HITL cues in the description field,
    # which would be invisible if we stripped frontmatter first.
    full_text = _read_skill_text(skill_dir)
    return {
        "mode": "skill",
        "input": str(skill_dir),
        "traits": {
            "has_references": _verdict_to_dict(has_references_skill(skill_dir)),
            "has_phases": _verdict_to_dict(has_phases_any(full_text)),
            "has_hitl": _verdict_to_dict(has_hitl_any(full_text)),
            "is_scheduled": _verdict_to_dict(is_scheduled_any(full_text)),
            "invokes_skills": _verdict_to_dict(
                invokes_skills_skill(skill_dir, ecosystem=ecosystem)
            ),
        },
    }


def _verdict_to_dict(v: Verdict) -> dict:
    return {"fires": v.fires, "evidence": v.evidence}


# ---------- CLI ----------


def _main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("spec", "skill"):
        print(
            "usage: python3 trait_predicates.py <spec|skill> <path> [--ecosystem <dir>]",
            file=sys.stderr,
        )
        return 2
    mode = argv[1]
    path = Path(argv[2]).expanduser().resolve()
    ecosystem = DEFAULT_ECOSYSTEM
    if "--ecosystem" in argv:
        i = argv.index("--ecosystem")
        if i + 1 < len(argv):
            ecosystem = Path(argv[i + 1]).expanduser().resolve()
    if mode == "spec":
        if not path.is_file():
            print(f"error: spec path is not a file: {path}", file=sys.stderr)
            return 1
        result = classify_spec(path, ecosystem=ecosystem)
    else:
        if not path.is_dir():
            print(f"error: skill path is not a directory: {path}", file=sys.stderr)
            return 1
        result = classify_skill(path, ecosystem=ecosystem)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
