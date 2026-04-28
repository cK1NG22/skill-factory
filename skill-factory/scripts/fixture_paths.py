#!/usr/bin/env python3
"""
fixture_paths.py — repo-root resolver for the `{{REPO_ROOT}}` placeholder
convention used in factory fixture files.

Static fixture inputs (e.g. `skill-frontmatter/fixtures/passing-input.md`)
and oracle outputs (e.g. `skill-spec-validator/fixtures/expected-pass.md`)
embed pattern paths and self-references. Hardcoding the absolute path of
the original author's clone made every fixture unusable elsewhere. The fix:
fixtures carry the literal token `{{REPO_ROOT}}` and consumers expand it
against this script's `__file__` anchor at read time.

Anchor: `Path(__file__).resolve().parents[2]` — i.e.
`skill-factory/scripts/fixture_paths.py` → `skill-factory/scripts/` →
`skill-factory/` → repo root. If you move this file, update parents[N]
or the resolver will silently anchor wrong.

Usage:
    # CLI — print expanded fixture content to stdout
    python3 skill-factory/scripts/fixture_paths.py <fixture-path>

    # Library
    from fixture_paths import repo_root, expand_repo_root
    expanded = expand_repo_root(raw_text)

Exit codes (CLI):
    0 — fixture read and expanded successfully
    1 — fixture path does not exist or is not a file
    2 — usage error (no path given)
"""
from __future__ import annotations

import sys
from pathlib import Path

PLACEHOLDER = "{{REPO_ROOT}}"


def repo_root(anchor: Path | None = None) -> Path:
    """Return the absolute repo root.

    `anchor` lets tests inject a fake __file__ location. When omitted, the
    body looks up the real anchor — defining it inline (rather than as a
    signature default) keeps `mock.patch.object` interception live per
    feedback-default-args-and-mock-patch.md (Stage 11a incident eee5140).
    """
    if anchor is None:
        anchor = Path(__file__).resolve()
    return anchor.parents[2]


def expand_repo_root(text: str, root: Path | None = None) -> str:
    """Substitute every `{{REPO_ROOT}}` occurrence with the absolute repo
    root. Idempotent: input without the placeholder is returned unchanged.
    """
    if root is None:
        root = repo_root()
    return text.replace(PLACEHOLDER, str(root))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: fixture_paths.py <fixture-path>", file=sys.stderr)
        return 2
    fixture = Path(argv[1])
    if not fixture.is_file():
        print(f"error: not a file: {fixture}", file=sys.stderr)
        return 1
    sys.stdout.write(expand_repo_root(fixture.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
