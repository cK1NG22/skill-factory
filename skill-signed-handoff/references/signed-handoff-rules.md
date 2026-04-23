# Signed-handoff rules — authoritative contract

Six rules govern a signature script emitted by `skill-signed-handoff`. Each
rule is checked mechanically by `scripts/handoff_lint.py`. When this document
and the lint script diverge, **the lint is authoritative** — update this
document to match the lint, not the other way around (factory convention per
the `skill-frontmatter` and `skill-phase-designer` precedents).

The rules assume the signature script follows the BP-024 handoff shape: an
upstream skill's terminal phase writes a signature; a downstream skill's
entry phase verifies it. The signature is a sha256 digest over a canonical
JSON serialization of a named subset of the upstream payload (the
"argument-bearing fields").

---

## Rule A — The script exposes a `--sign` mode

The generated script must accept a `--sign` CLI token (either as an
`argparse` flag, an `argv[1] == "--sign"` check, or any quoted literal that
contains the `--sign` string). Without a sign mode there is nothing for the
upstream phase to call.

**Correct:** `parser.add_argument("--sign", action="store_true", ...)`.

**Incorrect:** A script that only verifies and expects signatures to be
hand-written.

The lint greps the source for a `"--sign"` / `'--sign'` literal. A script
that names the mode `sign` (without the leading `--`) still passes because
the same literal appears inside argparse's rendered usage string, but using
`--sign` is the factory convention.

---

## Rule B — The script exposes a `--verify` mode

Mirror of Rule A: the generated script must accept a `--verify` CLI token.
Without it, the downstream phase cannot check the signature.

The lint enforces the `"--verify"` / `'--verify'` literal.

---

## Rule C — The script uses `hashlib.sha256`

Two checks:

1. The file imports `hashlib` (either `import hashlib` or
   `from hashlib import sha256`).
2. The file calls `hashlib.sha256(...)` or a bare `sha256(...)` somewhere.

Why both: importing without calling is dead code; calling `sha256(...)`
without an import means the name resolves to something other than the stdlib
primitive (likely a bug). A missing sha256 call also means the "signature"
is just an echo of the payload — useless.

Other hash functions (`md5`, `sha1`, `blake2b`) are NOT acceptable
substitutes. The BP-024 contract is sha256 specifically so every pipeline
emits comparable digests. Changing this requires a new BP.

---

## Rule D — A non-empty signed-fields literal is declared

The module must define a top-level list or tuple whose identifier contains
`FIELD` (case-insensitive), e.g.:

```python
SIGNED_FIELDS = [
    "argument_flow",
    "leadlines",
    "callout_items",
    "recommendation",
]
```

Acceptable alternatives: `FIELDS`, `HANDOFF_FIELDS`, `SIGNED_FIELDS_V1`.

The list must contain at least one entry and every entry must be a string
literal. Dynamic construction (loading from JSON, reading from env, list
comprehensions) is rejected — the lint cannot verify coverage against a
computed list, and the rules contract exists so the generated script is
auditable on its face.

An empty list is rejected: a signature over zero fields hashes the empty
dict for every payload, which is useless.

---

## Rule E — Exit codes 0, 1, 2, 3 are all reachable

The BP-024 contract defines four exit codes:

| Code | Meaning |
|------|---------|
| 0    | success (signed, or verified) |
| 1    | a SIGNED_FIELDS entry is missing from the payload |
| 2    | signature mismatch (payload drifted after signing) |
| 3    | I/O error (file missing, unreadable, malformed JSON) |

The lint walks the AST looking for `sys.exit(<int>)`, `exit(<int>)`,
`raise SystemExit(<int>)`, and `return <int>` statements with literal
integer arguments. All four codes must appear as reachable literals. It
also sweeps the raw source text for `sys.exit(<int>)` patterns as a
defense in depth.

Using constants (`EXIT_OK = 0`) is allowed as long as a call site passes the
literal integer somewhere — the lint does not resolve named constants.
In practice, using the literal integers directly inside `sys.exit(...)` is
simpler and survives rename refactors.

---

## Rule F — Canonical JSON serialization before hashing

The script must serialize the signed-fields subset in a canonical form
before hashing, otherwise dict-ordering drift between Python runs (even the
same version, same interpreter) can produce different digests for payloads
that are logically identical.

The lint accepts either:

- `json.dumps(..., sort_keys=True, ...)` anywhere in the source, OR
- an explicit `sorted(...)` call that the author uses to produce a stable
  key order before serialization.

The factory convention is `json.dumps(subset, sort_keys=True,
separators=(",", ":"), ensure_ascii=False).encode("utf-8")` — tight
separators remove whitespace drift, `sort_keys=True` removes dict-order
drift, and `ensure_ascii=False` keeps Unicode payloads byte-stable across
platforms that default differently. The template ships this exact call.

---

## What the lint does NOT check

- **Content of the fields.** If the upstream skill writes `leadlines: ""`
  (an empty string), the signature still verifies — Rule D only requires
  the field be present, not meaningful. The upstream skill's own lint is
  responsible for content quality.
- **Key aliasing.** A payload with `argument_flow_v2` instead of
  `argument_flow` will fail verification at runtime with exit code 1. The
  lint does not detect that the SIGNED_FIELDS list drifted from the
  upstream skill's actual outputs — that is a driver-level concern.
- **Signature file format.** The lint does not require a particular shape
  for the signature file (hex vs base64, trailing newline, …). The
  template writes hex + `\n`; any consistent format is acceptable as long
  as `--sign` and `--verify` agree.
- **Cryptographic strength.** sha256 is mandated, not HMAC-sha256. The
  signature is an integrity check, not an authentication primitive — the
  handoff is trusted within a single agent session, not across parties.
