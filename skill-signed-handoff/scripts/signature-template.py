#!/usr/bin/env python3
"""
{skill_slug}_signature.py — signed handoff between pipeline phases (BP-024).

Generated from skill-signed-handoff/scripts/signature-template.py. Edit the
SIGNED_FIELDS list and the module docstring to describe the upstream skill's
argument-bearing contract; leave the --sign / --verify plumbing intact so
`scripts/handoff_lint.py` stays green.

The canonical serialization is ``json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=False).encode("utf-8")``. Any change to
that line changes every signature this script has ever produced — do not
tweak the separators lightly.

Usage:
    python3 {skill_slug}_signature.py --sign   <payload.json> <signature.txt>
    python3 {skill_slug}_signature.py --verify <payload.json> <signature.txt>

Exit codes:
    0 — success (signed, or verified)
    1 — a SIGNED_FIELDS entry is missing from the payload
    2 — signature mismatch (payload has drifted since it was signed)
    3 — I/O error (file missing, unreadable, or malformed JSON)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Argument-bearing fields this handoff contract signs. ORDER IS NOT LOAD-
# BEARING (we sort keys at serialization time), but the SET of names is —
# add a field here only if upstream writers and downstream readers both
# update at the same time.
# ---------------------------------------------------------------------------
SIGNED_FIELDS: list[str] = [
    # Replace these placeholders with the upstream skill's real fields.
    "argument_flow",
    "leadlines",
    "callout_items",
    "recommendation",
]


def _load_payload(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"error: cannot read payload {path}: {e}", file=sys.stderr)
        sys.exit(3)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: payload {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(3)
    if not isinstance(obj, dict):
        print(f"error: payload {path} must be a JSON object at the top level", file=sys.stderr)
        sys.exit(3)
    return obj


def _canonical_subset(payload: dict) -> dict:
    """Pick SIGNED_FIELDS from the payload. Fail with exit 1 if any is missing."""
    missing = sorted(set(SIGNED_FIELDS) - set(payload.keys()))
    if missing:
        print(f"error: payload is missing signed fields: {missing}", file=sys.stderr)
        sys.exit(1)
    return {k: payload[k] for k in SIGNED_FIELDS}


def compute_signature(payload: dict) -> str:
    """Return the hex sha256 digest of the canonical JSON encoding."""
    subset = _canonical_subset(payload)
    encoded = json.dumps(
        subset,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sign(payload_path: Path, signature_path: Path) -> int:
    payload = _load_payload(payload_path)
    digest = compute_signature(payload)
    try:
        signature_path.write_text(digest + "\n", encoding="utf-8")
    except OSError as e:
        print(f"error: cannot write signature {signature_path}: {e}", file=sys.stderr)
        return 3
    return 0


def verify(payload_path: Path, signature_path: Path) -> int:
    payload = _load_payload(payload_path)
    try:
        expected = signature_path.read_text(encoding="utf-8").strip()
    except OSError as e:
        print(f"error: cannot read signature {signature_path}: {e}", file=sys.stderr)
        return 3
    actual = compute_signature(payload)
    if expected != actual:
        print(
            f"error: signature mismatch (expected {expected!r}, got {actual!r})",
            file=sys.stderr,
        )
        return 2
    return 0


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Signed-handoff sha256 tool")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sign", action="store_true", help="Write a fresh signature.")
    mode.add_argument("--verify", action="store_true", help="Check an existing signature.")
    parser.add_argument("payload", type=Path, help="Path to the JSON payload.")
    parser.add_argument("signature", type=Path, help="Path to the signature file.")
    args = parser.parse_args(argv[1:])
    if args.sign:
        return sign(args.payload, args.signature)
    return verify(args.payload, args.signature)


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
