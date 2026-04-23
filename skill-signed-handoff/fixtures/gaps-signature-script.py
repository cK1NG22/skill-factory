#!/usr/bin/env python3
"""
gaps example — a deliberately broken signature script used to exercise the
lint's blocking behavior. This file should FAIL handoff_lint.py.

Problems injected:
    - Uses md5 instead of sha256 (Rule C fails).
    - Has no `--verify` mode (Rule B fails).
    - SIGNED_FIELDS is empty (Rule D fails).
    - Missing sys.exit(2) and sys.exit(3) call sites (Rule E fails).
    - Does not sort keys before hashing (Rule F fails).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SIGNED_FIELDS: list[str] = []  # empty — Rule D violation


def sign(payload_path: Path, sig_path: Path) -> int:
    raw = payload_path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    encoded = json.dumps(payload).encode("utf-8")  # no sort_keys — Rule F
    digest = hashlib.md5(encoded).hexdigest()  # wrong algo — Rule C
    sig_path.write_text(digest + "\n", encoding="utf-8")
    return 0


def _main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] != "--sign":
        print("usage: --sign payload sig", file=sys.stderr)
        sys.exit(1)
    return sign(Path(argv[2]), Path(argv[3]))


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
