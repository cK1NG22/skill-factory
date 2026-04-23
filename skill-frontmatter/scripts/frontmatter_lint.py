#!/usr/bin/env python3
"""
frontmatter_lint.py — deterministic lint for a skill's YAML frontmatter block.

Implements the contract in references/frontmatter-rules.md. Pure stdlib — no
YAML parser dependency (we use a tiny hand-rolled scanner sufficient for
frontmatter's flat structure).

Exit codes:
    0 — lint passes
    1 — lint fails (at least one rule violated)
    2 — bad usage / I/O error

Usage:
    python3 frontmatter_lint.py <path-to-file-containing-frontmatter>
    python3 frontmatter_lint.py -  # reads frontmatter from stdin
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- Rule 1 — Name ---
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_RESERVED_NAMES = {"anthropic", "claude", "claude-code", "default"}

# --- Rule 4 — allowed-tools ---
_KNOWN_TOOLS = {
    "Read", "Write", "Edit",
    "Bash",
    "Glob", "Grep",
    "WebFetch", "WebSearch",
    "AskUserQuestion",
    "Agent",
    "TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TaskOutput", "TaskStop",
    "NotebookEdit",
    "ExitPlanMode", "EnterPlanMode",
}

_ALLOWED_TOP_KEYS = {
    "name", "description", "allowed-tools",
    "argument-hint", "model",
}

# --- Rule 3 — trigger phrases: quoted substrings containing a space ---
_QUOTED_PHRASE = re.compile(
    r"""(?:"([^"]{2,})"|'([^']{2,})')""",
    re.DOTALL,
)


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


def extract_frontmatter(text: str) -> str | None:
    """
    Extract the YAML frontmatter block from a markdown/text file. Returns the
    raw string between the opening `---` and the closing `---`, or None if no
    well-formed frontmatter block is present.
    """
    if not text.lstrip().startswith("---"):
        return None
    # Find the first `---` line
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start = i
            break
    if start is None:
        return None
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[start + 1 : i])
    return None


def _parse_flat_yaml(fm: str) -> dict:
    """
    Minimal YAML parser sufficient for flat frontmatter:
      key: value
      key: >-
        multi
        line
      key:
        - item1
        - item2

    Not a general YAML implementation. Good enough for frontmatter rules.
    """
    result: dict = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith(" ") or line.startswith("\t"):
            # indented continuation with no prior key — malformed, skip
            i += 1
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key = m.group(1)
        rest = m.group(2)
        # List form: next lines indented with "- "
        if rest == "":
            items = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                # Stop on frontmatter delimiter (handles being called on raw
                # `---\n...---\n` string without prior extract_frontmatter).
                if next_line.strip() == "---":
                    break
                if re.match(r"^\s*-\s", next_line):
                    item = re.sub(r"^\s*-\s*", "", next_line).strip()
                    # strip surrounding quotes
                    if (item.startswith('"') and item.endswith('"')) or (
                        item.startswith("'") and item.endswith("'")
                    ):
                        item = item[1:-1]
                    items.append(item)
                    j += 1
                elif next_line.strip() == "" or next_line.startswith((" ", "\t")):
                    j += 1
                else:
                    break
            result[key] = items
            i = j
            continue
        # Folded-scalar form: ">-" or ">" or "|"
        if rest in (">-", ">", "|", "|-"):
            chunks = []
            j = i + 1
            while j < len(lines) and (lines[j].startswith((" ", "\t")) or lines[j].strip() == ""):
                chunks.append(lines[j].strip())
                j += 1
            result[key] = " ".join(c for c in chunks if c)
            i = j
            continue
        # Quoted-string form
        if (rest.startswith('"') and rest.endswith('"')) or (
            rest.startswith("'") and rest.endswith("'")
        ):
            result[key] = rest[1:-1]
        else:
            result[key] = rest
        i += 1
    return result


def lint(fm_text: str) -> LintResult:
    fails: list[str] = []
    warns: list[str] = []
    info: list[str] = []

    parsed = _parse_flat_yaml(fm_text)

    # --- Rule: required keys present ---
    for required in ("name", "description", "allowed-tools"):
        if required not in parsed:
            fails.append(f"required key missing: {required!r}")

    # --- Rule: no unknown top-level keys ---
    unknown = sorted(set(parsed.keys()) - _ALLOWED_TOP_KEYS)
    for key in unknown:
        warns.append(f"unknown top-level key: {key!r} (allowed: {sorted(_ALLOWED_TOP_KEYS)})")

    # --- Rule 1: name ---
    name = parsed.get("name", "")
    if name:
        if not _NAME_RE.match(name):
            fails.append(
                f"name {name!r} violates ^[a-z][a-z0-9-]{{1,63}}$ "
                f"(must start with a lowercase letter; lowercase+digits+hyphens only; 2-64 chars)"
            )
        if name in _RESERVED_NAMES:
            fails.append(f"name {name!r} is reserved (blocked: {sorted(_RESERVED_NAMES)})")

    # --- Rule 2: description length ---
    desc = parsed.get("description", "")
    if desc:
        if len(desc) > 1024:
            fails.append(f"description is {len(desc)} chars (max 1024)")
        elif len(desc) < 80:
            fails.append(f"description is {len(desc)} chars (min 80 — too terse for trigger matching)")
        else:
            info.append(f"description length: {len(desc)} chars")

    # --- Rule 3: trigger phrases in description ---
    if desc:
        matches = _QUOTED_PHRASE.findall(desc)
        phrases = [a or b for (a, b) in matches if (a or b).strip()]
        # Filter to phrases containing a space (likely to be user speech, not single words)
        phrases_with_space = [p for p in phrases if " " in p]
        if len(phrases_with_space) < 3:
            fails.append(
                f"description contains {len(phrases_with_space)} quoted trigger phrase(s) with a space; "
                f"need at least 3 (BP-001). Phrases found: {phrases_with_space}"
            )
        elif len(phrases_with_space) < 5:
            warns.append(
                f"description has only {len(phrases_with_space)} trigger phrases; factory target is 5–10 "
                f"for robust dispatching"
            )
        else:
            info.append(f"trigger phrases detected: {len(phrases_with_space)}")

    # --- Rule 5: negative-case clause (soft) ---
    # Accept "do not use for X", "do not use to X", "don't use for/to X".
    if desc and not re.search(
        r"\b(?:do\s+not|don't)\s+use\s+(?:for|to)\b", desc, re.IGNORECASE
    ):
        warns.append(
            "description lacks a 'Do NOT use for X' negative clause; "
            "factory recommends one to improve trigger precision (BP-002)"
        )

    # --- Rule 4: allowed-tools ---
    tools = parsed.get("allowed-tools", None)
    if tools is None:
        # already flagged as missing required key above; skip
        pass
    elif not isinstance(tools, list):
        fails.append(f"allowed-tools must be a YAML list; got {type(tools).__name__}")
    elif len(tools) == 0:
        warns.append(
            "allowed-tools is an empty list; only valid for pure-text skills that never touch tools"
        )
    else:
        unknown_tools = [t for t in tools if t not in _KNOWN_TOOLS and not t.startswith("mcp__")]
        if unknown_tools:
            warns.append(
                f"unrecognized tools (allowed if intentional MCP/custom): {unknown_tools}; "
                f"known tools: {sorted(_KNOWN_TOOLS)}"
            )
        info.append(f"allowed-tools declared: {tools}")

    return LintResult(fails=fails, warns=warns, info=info)


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 frontmatter_lint.py <path-or->", file=sys.stderr)
        return 2
    src = argv[1]
    if src == "-":
        text = sys.stdin.read()
    else:
        p = Path(src).expanduser().resolve()
        if not p.is_file():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
        text = p.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if fm is None:
        result = LintResult(
            fails=["no frontmatter block found (must start with '---' and end with '---')"],
            warns=[],
            info=[],
        )
    else:
        result = lint(fm)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
