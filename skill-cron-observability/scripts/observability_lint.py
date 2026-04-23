#!/usr/bin/env python3
"""
observability_lint.py — deterministic lint for the BP-022 cron observability
contract, applied to a generated instrumentation snippet or to an existing
skill's scripts/ directory.

Implements the 4 rules in references/cron-observability-rules.md. Pure stdlib.

Usage:
    python3 observability_lint.py <path-to-snippet.md-or-scripts-dir>
    python3 observability_lint.py -                 # reads from stdin

Accepts:
    - A single .md file containing one or more fenced ```python code blocks.
      All fenced blocks are concatenated and scanned.
    - A single .py file. Scanned as-is.
    - A directory. Every .py file in the directory (non-recursive) is
      concatenated and scanned.
    - '-' to read raw code/markdown from stdin.

Exit codes:
    0 — lint passes (all 4 rules satisfied)
    1 — lint fails (at least one rule violated)
    2 — bad usage / I/O error
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Rule A — a `result.json` path segment under a runs/<timestamp>/ directory.
# Accept both forward-slash and backslash-less patterns because generated code
# may interpolate via pathlib or f-strings. The core requirement: the string
# literal "result.json" appears somewhere AND the code references a runs/
# directory with a timestamp-shaped component.
_RESULT_JSON_LITERAL = re.compile(r"""["']result\.json["']""")
# Accept:
#   - "runs/" or "runs\\" inside string literals
#   - pathlib construction: "runs" as a quoted component (e.g. Path(...) / "runs" / ts)
#   - variable names like run_dir / runs_dir — lower-confidence but caught
_RUNS_DIR_REF = re.compile(
    r"""(?:runs[/\\])|(?:["']runs["'])|(?:\brun_dir\b)|(?:\bruns_dir\b)"""
)
# Timestamp pattern accepts common iso8601-ish forms used in directory names
# (e.g. 20260423T171530Z, 2026-04-23T17:15:30Z, utcnow().strftime(...)).
_TIMESTAMP_REF = re.compile(
    r"""(?:
        utcnow\s*\(\s*\)           # datetime.datetime.utcnow()
      | now\s*\(\s*\)\.isoformat   # .now().isoformat
      | strftime                   # any strftime call
      | datetime\.now              # datetime.now
      | isoformat                  # plain isoformat reference
      | \d{4}-?\d{2}-?\d{2}T       # literal iso-shaped prefix
    )""",
    re.VERBOSE,
)

# Rule B — artifact file write. We look for either an "artifact" string
# literal OR a write of a file with a non-json extension inside run_dir.
_ARTIFACT_LITERAL = re.compile(
    r"""["']artifact(?:\.[A-Za-z0-9]{1,8})?["']"""
)
# A secondary accept-pattern: a string/f-string literal containing a filename
# with a non-.json extension (e.g. "out.csv", "digest.md", f"out.{EXT}"), OR
# the special "artifact.<ext>" pattern (already caught by _ARTIFACT_LITERAL
# but redundantly accepted here for clarity).
# Must be inside quotes to count — bare attribute accesses like `.dumps` or
# method chains like `.write_text(...)` must not false-positive.
_WRITE_NONJSON_NEAR_RUN = re.compile(
    r"""["']
    [^"'\n]{0,64}           # filename prefix
    \.(?!json["'])          # a dot NOT followed by "json"
    (?:[A-Za-z0-9]{1,8}|\{[A-Za-z_][A-Za-z0-9_]*\})  # ext OR {ext} f-string slot
    ["']
    """,
    re.VERBOSE,
)

# Rule C — latest.json pointer (symlink preferred, file write acceptable).
_LATEST_JSON = re.compile(r"""["']latest\.json["']""")
_SYMLINK_OP = re.compile(r"""symlink_to|os\.symlink|\.symlink\(""")

# Rule D — result.json content must include keys last_run, success, artifact_path.
# We regex-search for each key as a string literal. This catches both dict
# literal form ({"last_run": ...}) and json.dumps-over-dict construction
# (result = {...; "last_run": ...}).
_KEY_LAST_RUN = re.compile(r"""["']last_run["']""")
_KEY_SUCCESS = re.compile(r"""["']success["']""")
_KEY_ARTIFACT_PATH = re.compile(r"""["']artifact_path["']""")

# Fenced python block extractor. Accepts ```python, ```py, or bare ``` (rare).
_FENCED_PYTHON_BLOCK = re.compile(
    r"""```(?:python|py)?\s*\n(.*?)```""",
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


def extract_code(text: str, source_is_markdown: bool) -> str:
    """Return the scannable code body.

    If the source is markdown, concatenate every fenced python block. If no
    fenced blocks are found in markdown, return the empty string — the caller
    should then report a targeted fail rather than scanning the prose.

    If the source is raw .py, return text unchanged.
    """
    if not source_is_markdown:
        return text
    blocks = _FENCED_PYTHON_BLOCK.findall(text)
    return "\n\n".join(blocks)


def lint(code: str, *, had_fences: bool | None = None) -> LintResult:
    """Run the 4 BP-022 rules against `code`. `had_fences` is a tri-state:
    - None: caller did not extract from markdown (raw .py input).
    - True: markdown source, fenced python blocks found and concatenated.
    - False: markdown source, NO fenced blocks found — emit targeted fail.
    """
    fails: list[str] = []
    warns: list[str] = []
    info: list[str] = []

    if had_fences is False:
        fails.append(
            "no fenced ```python code block found in markdown input; "
            "observability_lint cannot scan prose alone"
        )
        return LintResult(fails=fails, warns=warns, info=info)

    if not code.strip():
        fails.append("empty code body; nothing to lint")
        return LintResult(fails=fails, warns=warns, info=info)

    # Rule A — result.json under runs/<timestamp>/
    has_result_json = bool(_RESULT_JSON_LITERAL.search(code))
    has_runs_dir = bool(_RUNS_DIR_REF.search(code))
    has_timestamp = bool(_TIMESTAMP_REF.search(code))
    if not has_result_json:
        fails.append(
            "Rule A: no 'result.json' string literal found; BP-022 requires "
            "writing ~/Claude/<skill>/runs/<timestamp>/result.json"
        )
    else:
        info.append("Rule A: 'result.json' literal present")
    if not has_runs_dir:
        fails.append(
            "Rule A: no 'runs/' path segment found; BP-022 requires a "
            "~/Claude/<skill>/runs/<timestamp>/ directory layout"
        )
    if not has_timestamp:
        fails.append(
            "Rule A: no timestamp construction found (utcnow/strftime/"
            "isoformat); BP-022 requires a unique per-run timestamp "
            "directory"
        )

    # Rule B — artifact file write
    has_artifact_literal = bool(_ARTIFACT_LITERAL.search(code))
    has_nonjson_write_near_run = bool(_WRITE_NONJSON_NEAR_RUN.search(code))
    if not (has_artifact_literal or has_nonjson_write_near_run):
        fails.append(
            "Rule B: no artifact file write detected; BP-022 requires "
            "writing ~/Claude/<skill>/runs/<timestamp>/artifact.<ext> "
            "alongside result.json"
        )
    else:
        info.append("Rule B: artifact file write detected")

    # Rule C — latest.json pointer
    has_latest_literal = bool(_LATEST_JSON.search(code))
    has_symlink_op = bool(_SYMLINK_OP.search(code))
    if not has_latest_literal:
        fails.append(
            "Rule C: no 'latest.json' string literal found; BP-022 requires "
            "maintaining ~/Claude/<skill>/latest.json as a pointer to the "
            "most recent run's result.json"
        )
    elif not has_symlink_op:
        warns.append(
            "Rule C: 'latest.json' referenced but no symlink_to/os.symlink "
            "call detected; a file copy is acceptable but a symlink is "
            "preferred for atomicity (BP-022)"
        )
        info.append("Rule C: 'latest.json' present (as file write)")
    else:
        info.append("Rule C: 'latest.json' symlink present")

    # Rule D — result.json content keys
    missing_keys = []
    if not _KEY_LAST_RUN.search(code):
        missing_keys.append("last_run")
    if not _KEY_SUCCESS.search(code):
        missing_keys.append("success")
    if not _KEY_ARTIFACT_PATH.search(code):
        missing_keys.append("artifact_path")
    if missing_keys:
        fails.append(
            f"Rule D: result.json is missing required key(s): {missing_keys}. "
            f"BP-022 requires keys 'last_run' (iso8601), 'success' (bool), "
            f"'artifact_path' (str)"
        )
    else:
        info.append("Rule D: all 3 result.json keys present")

    return LintResult(fails=fails, warns=warns, info=info)


def _read_source(src: str) -> tuple[str, bool | None]:
    """Return (code_text, had_fences) for the given source path or '-'.

    had_fences is True/False when the source is markdown, None for raw code.
    """
    if src == "-":
        text = sys.stdin.read()
        # Treat stdin as markdown iff it contains a fenced block opener.
        if "```" in text:
            blocks = _FENCED_PYTHON_BLOCK.findall(text)
            return ("\n\n".join(blocks), bool(blocks))
        return (text, None)
    p = Path(src).expanduser().resolve()
    if p.is_dir():
        # Concatenate every .py file at top level (non-recursive)
        py_files = sorted(p.glob("*.py"))
        if not py_files:
            return ("", None)
        parts = []
        for pf in py_files:
            parts.append(pf.read_text(encoding="utf-8"))
        return ("\n\n".join(parts), None)
    if not p.is_file():
        raise FileNotFoundError(f"file not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".md":
        blocks = _FENCED_PYTHON_BLOCK.findall(text)
        return ("\n\n".join(blocks), bool(blocks))
    return (text, None)


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: observability_lint.py <path-or->",
            file=sys.stderr,
        )
        return 2
    try:
        code, had_fences = _read_source(argv[1])
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    result = lint(code, had_fences=had_fences)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
