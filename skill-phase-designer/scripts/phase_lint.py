#!/usr/bin/env python3
"""
phase_lint.py — deterministic lint for a skill's ## Procedure section.

Implements the 6 rules in references/phase-design-rules.md. Pure stdlib.

Usage:
    python3 phase_lint.py <path-to-procedure-md> [--hitl] [--invokes-skills]
    python3 phase_lint.py - [--hitl]                # reads from stdin

Rules 1-3 apply universally (when has_phases fires).
Rules 4-6 apply only when --hitl is passed.

Exit codes:
    0 — lint passes
    1 — lint fails
    2 — bad usage / I/O error
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Canonical imperative-verb list (case-insensitive match on the first word of
# a step body). Includes control keywords that are acceptable as step openers.
_IMPERATIVE_VERBS = {
    # core action verbs
    "read", "write", "parse", "invoke", "check", "validate", "ensure", "add",
    "run", "print", "fetch", "consult", "assemble", "present", "prompt", "ask",
    "wait", "do", "set", "return", "exit", "create", "delete", "compute",
    "evaluate", "emit", "announce", "stop", "continue", "capture", "strip",
    "walk", "generate", "build", "render", "process", "extract", "verify",
    "save", "load", "open", "close", "move", "copy", "apply", "try", "catch",
    "raise", "log", "scan", "lint", "output", "materialize", "spawn", "compose",
    "draft", "signal", "gate", "collect", "pick", "select", "test", "record",
    "register", "install", "uninstall", "mount", "unmount", "push", "pop",
    "append", "prepend", "insert", "remove", "replace", "rename", "retry",
    "skip", "resume", "classify", "tag", "mark", "flag", "unify", "merge",
    "split", "join", "group", "sort", "normalize", "resolve", "reject",
    "accept", "confirm", "use", "update", "upload", "download", "hand",
    "answer", "respond", "reply", "notify", "warn", "report", "surface",
    "escalate", "abort", "fail", "succeed", "begin", "end", "start", "finish",
    "note", "remember", "forget", "clear", "reset", "prepare", "clean",
    # control-flow keywords acceptable as step openers
    "if", "for", "while", "else", "when", "after", "before",
}

# Case-insensitive substrings that indicate weak or passive voice.
_WEAK_PHRASES = [
    r"\bshould be\b",
    r"\bwill be\b",
    r"\bwe should\b",
    r"\byou should\b",
    r"\bit should\b",
    r"\bthe user should\b",
    r"\bwe will\b",
    r"\bmight want to\b",
    r"\btry to\b",
    r"\battempt to\b",
    r"\bconsider \w+ing\b",
    r"\bit is recommended\b",
    r"\bthe system will\b",
]

# Regex for a step heading like "### Step 1 — Label"
_STEP_HEADING = re.compile(r"^###\s+Step\s+(\d+)\s+—\s+(.+?)\s*$", re.MULTILINE)

# Regex for a numbered list item "1. question?" — line-level, no multiline
# anchors so we can check individual lines without \n-greedy \s* issues.
_NUMBERED_QUESTION_LINE = re.compile(r"^[ \t]*\d+[\.\)][ \t]+.+\?[ \t]*$")

# Hard-gate phrase
_HARD_GATE = re.compile(r"\bDo\s+NOT\s+proceed\b")

# AskUserQuestion token (bare word or call form)
_ASK_USER_QUESTION = re.compile(r"\bAskUserQuestion\b")


@dataclass
class LintResult:
    fails: list[str]
    warns: list[str]
    info: list[str]

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
    """Remove fenced code blocks so rules don't false-match on shell examples."""
    return re.sub(r"```[\s\S]*?```", "", text)


def _extract_steps(text: str) -> list[tuple[int, str, str]]:
    """Return list of (step_number, label, body_text). body_text is the
    content between this heading and the next Step heading (or end of text)."""
    matches = list(_STEP_HEADING.finditer(text))
    out: list[tuple[int, str, str]] = []
    for i, m in enumerate(matches):
        n = int(m.group(1))
        label = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((n, label, text[start:end].strip()))
    return out


def _first_word(text: str) -> str:
    """First English word of a step body, skipping leading markdown artifacts,
    inline-code spans, and slash-prefixed skill tokens. The goal is to surface
    the real action verb for Rule 2 error messages — a body opening with
    `` `/docx` renders the packet `` should report "renders" (non-imperative),
    not "empty body"."""
    stripped = re.sub(r"^[\s\*\-\_\>]+", "", text).strip()
    # Skip leading inline-code span(s) like `foo` or `/docx`
    while True:
        m = re.match(r"`[^`\n]*`\s*", stripped)
        if not m:
            break
        stripped = stripped[m.end():]
    # Skip a bare /slash-skill token that may appear without backticks
    m = re.match(r"/[a-z][a-z0-9-]*\s*", stripped)
    if m:
        stripped = stripped[m.end():]
    m = re.match(r"[A-Za-z]+", stripped)
    return m.group(0) if m else ""


def lint(
    text: str, has_hitl: bool = False, invokes_skills: bool = False
) -> LintResult:
    fails: list[str] = []
    warns: list[str] = []
    info: list[str] = []

    # Strip fenced code blocks for rules that could false-match on shell.
    scannable = _strip_code_fences(text)

    # Rule 1 — Steps are numbered and sequential
    # Soft check: warn if the '## Procedure' section header is absent. The
    # target SKILL.md needs it; without it, step headings live in an undeclared
    # section.
    if not re.search(r"^##\s+Procedure\s*$", scannable, re.MULTILINE):
        warns.append(
            "no '## Procedure' section header found; steps should live "
            "under a '## Procedure' section per factory convention"
        )
    # Also surface the "looks like a step heading but uses wrong separator"
    # case — easier to fix than a bare "no headings found".
    loose_step = re.search(
        r"^###\s+Step\s+\d+\s+[\-–]\s", scannable, re.MULTILINE
    )
    if loose_step and not _STEP_HEADING.search(scannable):
        fails.append(
            "step headings use '-' or '–'; factory convention requires '—' "
            "(em-dash, U+2014) between step number and label"
        )
    steps = _extract_steps(scannable)
    if not steps:
        fails.append("no '### Step N — <label>' headings found")
    else:
        numbers = [n for n, _, _ in steps]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            fails.append(
                f"step numbers are {numbers}; expected sequential {expected}"
            )
        else:
            info.append(f"{len(steps)} step(s) detected in sequence 1..{len(steps)}")

    # Rule 2 — Each step starts with an imperative verb
    for n, label, body in steps:
        fw = _first_word(body).lower()
        if not fw:
            fails.append(f"step {n} ({label!r}) has an empty body")
            continue
        if fw not in _IMPERATIVE_VERBS:
            fails.append(
                f"step {n} ({label!r}) starts with {fw!r}; not in canonical "
                f"imperative-verb list. See references/phase-design-rules.md Rule 2."
            )

    # Rule 3 — No weak/passive voice
    weak_hits: list[str] = []
    for pat in _WEAK_PHRASES:
        for m in re.finditer(pat, scannable, re.IGNORECASE):
            weak_hits.append(m.group(0))
    if weak_hits:
        fails.append(
            f"weak/passive voice detected ({len(weak_hits)} instance(s)): "
            f"{sorted(set(weak_hits))}"
        )

    # Rule 4 — At least one hard gate (only if has_hitl)
    if has_hitl:
        if not _HARD_GATE.search(scannable):
            fails.append(
                "no 'Do NOT proceed' hard gate found; BP-012 requires at least "
                "one when has_hitl fires"
            )
        else:
            gates = len(_HARD_GATE.findall(scannable))
            info.append(f"hard gates present: {gates}")

    # Rule 5 — Questions are numbered or use AskUserQuestion (only if has_hitl)
    # A "question line" is any line containing '?' anywhere (not just at the
    # end) — "Do you know the format? Then proceed." contains a user-facing
    # question even though the line doesn't terminate with '?'.
    if has_hitl:
        all_lines = scannable.splitlines()
        for idx, ln in enumerate(all_lines):
            if "?" not in ln:
                continue
            if _NUMBERED_QUESTION_LINE.match(ln):
                continue
            # Accept if AskUserQuestion appears in the same nearby block (± 3 lines)
            window = "\n".join(all_lines[max(0, idx - 3): idx + 4])
            if _ASK_USER_QUESTION.search(window):
                continue
            fails.append(
                f"question not numbered and no AskUserQuestion nearby: {ln.strip()!r}"
            )

    # Rule 6 — At most 4 inline questions (only if has_hitl)
    if has_hitl:
        # Count '?' outside quoted strings and code. Strip backtick spans and
        # double-quoted strings. Single-quote stripping was removed: it ate
        # prose between contractions (e.g., `don't … it's` spans matched as
        # quoted string and dropped `?` characters from the count).
        prose = re.sub(r"`[^`\n]*`", "", scannable)
        prose = re.sub(r'"[^"\n]*"', "", prose)
        q_count = prose.count("?")
        if q_count > 4:
            warns.append(
                f"{q_count} inline questions; BP-016 recommends moving "
                f"overflow (>{4}) to references/scoping-questions.md"
            )
        else:
            info.append(f"inline questions: {q_count} (within BP-016 limit)")

    if invokes_skills:
        info.append(
            "invokes_skills: true — signed-handoff discipline (BP-024) is a "
            "future skill-signed-handoff concern; no action needed here"
        )

    return LintResult(fails=fails, warns=warns, info=info)


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: phase_lint.py <path-or-> [--hitl] [--invokes-skills]",
            file=sys.stderr,
        )
        return 2
    src = argv[1]
    has_hitl = "--hitl" in argv[2:]
    invokes_skills = "--invokes-skills" in argv[2:]
    if src == "-":
        text = sys.stdin.read()
    else:
        p = Path(src).expanduser().resolve()
        if not p.is_file():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
        text = p.read_text(encoding="utf-8")
    result = lint(text, has_hitl=has_hitl, invokes_skills=invokes_skills)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
