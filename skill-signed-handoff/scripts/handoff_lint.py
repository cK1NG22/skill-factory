#!/usr/bin/env python3
"""
handoff_lint.py — deterministic lint for a signed-handoff signature script.

Implements the 6 rules in references/signed-handoff-rules.md. Pure stdlib.

A signed-handoff script is a small Python module that (a) signs a subset of
argument-bearing fields produced by an upstream skill by hashing a canonical
serialization with sha256, and (b) verifies the signature downstream. The
lint audits the script's source text (it does NOT execute the script).

Usage:
    python3 handoff_lint.py <path-to-signature-script>
    python3 handoff_lint.py -                           # reads from stdin

Exit codes:
    0 — lint passes
    1 — lint fails
    2 — bad usage / I/O error
"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


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


# Rule A/B — mode tokens we accept as evidence of --sign / --verify handling.
_SIGN_MODE_RE = re.compile(r"""['"]--sign['"]|['"]\bsign\b['"]""")
_VERIFY_MODE_RE = re.compile(r"""['"]--verify['"]|['"]\bverify\b['"]""")

# Rule C — sha256 usage.
_HASHLIB_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:import\s+hashlib\b|from\s+hashlib\s+import\s+[^\n]*)"
)
_SHA256_CALL_RE = re.compile(r"\bhashlib\.sha256\b|(?<!\w)sha256\s*\(")

# Rule F — canonical JSON serialization.
_SORT_KEYS_RE = re.compile(r"\bsort_keys\s*=\s*True\b")
_EXPLICIT_SORT_RE = re.compile(r"\bsorted\s*\(")


def _reachable_exit_codes(tree: ast.AST, source: str, scannable: str) -> set[int]:
    """Return the set of integer exit codes reachable from sys.exit(...),
    exit(...), SystemExit(...), or `return <int>` inside the module's main.

    Also sweeps the raw source for `sys.exit(<int>)` text as a defense in depth
    (handles string-based exit code constants we do not evaluate)."""
    codes: set[int] = set()

    def _record(arg: ast.expr) -> None:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
            codes.add(arg.value)
        elif isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
            # negative literal (e.g. -1) — unusual but possible
            inner = arg.operand
            if isinstance(inner, ast.Constant) and isinstance(inner.value, int):
                codes.add(-inner.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "sys" and func.attr == "exit":
                    name = "sys.exit"
            elif isinstance(func, ast.Name):
                if func.id in ("exit", "SystemExit"):
                    name = func.id
            if name and node.args:
                _record(node.args[0])
        elif isinstance(node, ast.Raise):
            exc = node.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                if exc.func.id == "SystemExit" and exc.args:
                    _record(exc.args[0])
        elif isinstance(node, ast.Return) and node.value is not None:
            # `return 0` / `return 2` inside a handler function that the
            # CLI entrypoint eventually hands to `sys.exit(...)` — count
            # each literal return as reaching that exit code.
            _record(node.value)

    # Text-level sweep as backup on the comment/docstring-stripped source,
    # so exit-code numbers mentioned in prose do not count as "reachable".
    for m in re.finditer(r"sys\.exit\s*\(\s*(-?\d+)\s*\)", scannable):
        try:
            codes.add(int(m.group(1)))
        except ValueError:
            pass
    for m in re.finditer(r"(?<!\w)exit\s*\(\s*(-?\d+)\s*\)", scannable):
        try:
            codes.add(int(m.group(1)))
        except ValueError:
            pass

    return codes


def _extract_signed_fields(tree: ast.AST) -> list[str] | None:
    """Find a module-level list/tuple literal assigned to a *FIELDS* identifier
    (e.g. SIGNED_FIELDS, FIELDS, HANDOFF_FIELDS). Returns the list of string
    items, or None if no such constant is declared as a literal.

    Nested / dynamic construction (e.g. `FIELDS = load_from_json()`) is not
    honored — the rules contract requires a declared literal so the lint can
    mechanically verify coverage."""
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if "FIELD" not in target.id.upper():
                continue
            if isinstance(value, (ast.List, ast.Tuple)):
                out: list[str] = []
                for elt in value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        out.append(elt.value)
                    else:
                        # mixed non-string elements → treat as undeclared
                        return None
                return out
    return None


def lint(source: str) -> LintResult:
    fails: list[str] = []
    warns: list[str] = []
    info: list[str] = []

    # Strip line comments to avoid false positives on patterns mentioned in
    # explanatory comments (e.g., "# use sort_keys=True for canonical form").
    # We preserve them in the AST parse below — only the regex sweeps see the
    # stripped form.
    scannable = re.sub(r"(?m)^[ \t]*#.*$", "", source)
    # Also drop standalone triple-quoted docstrings/blocks to prevent
    # docstrings that merely reference patterns from counting as evidence.
    scannable = re.sub(
        r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "", scannable
    )

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        fails.append(f"script has a Python syntax error: {e.msg} at line {e.lineno}")
        return LintResult(fails=fails, warns=warns, info=info)

    # Rule A — --sign mode
    if not _SIGN_MODE_RE.search(scannable):
        fails.append(
            "Rule A: no '--sign' mode token found. The script must accept a "
            "'--sign' argument (or equivalent) that writes the signature."
        )

    # Rule B — --verify mode
    if not _VERIFY_MODE_RE.search(scannable):
        fails.append(
            "Rule B: no '--verify' mode token found. The script must accept a "
            "'--verify' argument (or equivalent) that checks the signature."
        )

    # Rule C — hashlib.sha256 present
    has_import = bool(_HASHLIB_IMPORT_RE.search(source))
    has_call = bool(_SHA256_CALL_RE.search(scannable))
    if not has_import:
        fails.append(
            "Rule C: no 'import hashlib' (or 'from hashlib import …') found. "
            "Signatures must use sha256 from the stdlib."
        )
    if not has_call:
        fails.append(
            "Rule C: no 'hashlib.sha256(' or bare 'sha256(' call found. "
            "Importing hashlib is not enough — the script must call sha256."
        )

    # Rule D — signed-fields list declared, non-empty, all strings
    fields = _extract_signed_fields(tree)
    if fields is None:
        fails.append(
            "Rule D: no module-level list/tuple constant with 'FIELD' in its "
            "name (e.g., SIGNED_FIELDS = [...]) found. A signed-fields literal "
            "is required so the lint can verify coverage."
        )
    elif len(fields) == 0:
        fails.append(
            "Rule D: signed-fields list is empty; a signature over zero fields "
            "is useless. Declare at least one argument-bearing field."
        )
    else:
        info.append(f"signed fields declared: {fields}")

    # Rule E — exit codes 0, 1, 2, 3 all reachable
    codes = _reachable_exit_codes(tree, source, scannable)
    required_codes = {0, 1, 2, 3}
    missing = sorted(required_codes - codes)
    if missing:
        fails.append(
            f"Rule E: exit codes {missing} not reachable via sys.exit / exit / "
            f"SystemExit literal. All of 0 (success), 1 (missing field), "
            f"2 (signature mismatch), 3 (I/O error) must be present."
        )
    else:
        info.append(f"exit codes reachable: {sorted(codes & required_codes)}")

    # Rule F — canonical serialization (sort_keys=True or explicit sorted())
    if not (_SORT_KEYS_RE.search(scannable) or _EXPLICIT_SORT_RE.search(scannable)):
        fails.append(
            "Rule F: no canonical serialization detected. Use "
            "json.dumps(..., sort_keys=True) or explicit sorted() over keys "
            "before hashing — otherwise dict-order drift will mismatch."
        )

    return LintResult(fails=fails, warns=warns, info=info)


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 handoff_lint.py <path-or->", file=sys.stderr)
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
    result = lint(text)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
