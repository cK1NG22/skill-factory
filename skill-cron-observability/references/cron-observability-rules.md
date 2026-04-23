# Cron-observability rules — authoritative contract

Four rules govern the instrumentation any cron/scheduled skill (trait `is_scheduled: true`) must carry. Each rule is derived directly from BP-022 ("Cron/scheduled skills must expose last-run, success, artifact location").

The deterministic lint at `scripts/observability_lint.py` checks each rule mechanically. When this document and the lint script diverge, **the lint is authoritative** — update this document to match the lint, not the other way around (factory convention established by `skill-frontmatter` and `skill-phase-designer`).

---

## Rule A — result.json under runs/<timestamp>/ (BP-022)

The skill's cron code must write a `result.json` file to a per-run directory `~/Claude/<skill>/runs/<timestamp>/`.

The lint checks three sub-conditions:
1. The string literal `"result.json"` (or `'result.json'`) appears in the code.
2. The code references a `runs/` path segment.
3. The code constructs a timestamp via `utcnow()`, `strftime(...)`, `isoformat(...)`, `datetime.now(...)`, or embeds a literal ISO-8601 prefix (`YYYY-MM-DDT` or `YYYYMMDDT`).

**Why:** `result.json` is the machine-readable status record. Keeping it under a per-run timestamp directory preserves history — a failed run does not overwrite the last successful one.

**Correct:**
```python
timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
run_dir = Path.home() / "Claude" / "acme-weekly-digest" / "runs" / timestamp
run_dir.mkdir(parents=True, exist_ok=True)
(run_dir / "result.json").write_text(json.dumps(result))
```

**Incorrect:**
```python
# Overwrites the previous run's state
Path("~/Claude/acme-weekly-digest/status.json").expanduser().write_text(json.dumps(result))
```

---

## Rule B — artifact file written in the same directory (BP-022)

The skill must write the actual output (the digest, csv, docx, …) to a file named `artifact.<ext>` (or a clearly-non-json filename) inside the same `runs/<timestamp>/` directory.

The lint accepts either:
- A string literal `"artifact"` or `"artifact.<ext>"` in the code, OR
- A file write (`open(...)`, `write_text`, `write_bytes`, `Path(...)`, `savefig`, `to_csv`, `save(...)`) with a non-`.json` extension on the same line as a reference to `run_dir`, `runs/`, or a timestamp.

**Why:** A cron run without an artifact is a cron run with nothing to show. Keeping the artifact alongside `result.json` makes every historical run self-contained — one directory, two files, everything you need to debug.

**Correct:**
```python
artifact_path = run_dir / f"artifact.{ext}"
artifact_path.write_text(rendered_digest)
```

**Incorrect:**
```python
# Artifact scattered into /tmp; will be gone by next boot
Path("/tmp/digest.md").write_text(rendered_digest)
```

---

## Rule C — latest.json pointer at the skill root (BP-022)

The skill must maintain a `~/Claude/<skill>/latest.json` file or symlink that points to the most recent run's `result.json`.

The lint checks:
- The string literal `"latest.json"` appears in the code.
- A symlink operation (`symlink_to`, `os.symlink`, `.symlink(...)`) is present. A regular file write is accepted but produces a warning — symlinks are preferred because an atomic rename (`os.replace`) gives all-or-nothing semantics.

**Why:** "Is the skill healthy?" must be answerable in one read. Without a stable pointer, consumers have to list `runs/` and sort — slow, and racy during a run.

**Correct:**
```python
latest = Path.home() / "Claude" / "acme-weekly-digest" / "latest.json"
if latest.exists() or latest.is_symlink():
    latest.unlink()
latest.symlink_to(run_dir / "result.json")
```

**Incorrect:**
```python
# Consumer must list runs/ and sort — slow and racy
(run_dir / "result.json").write_text(json.dumps(result))
```

---

## Rule D — result.json includes last_run, success, artifact_path (BP-022)

The `result.json` content must include three keys at minimum:
- `last_run` — ISO-8601 timestamp (str).
- `success` — boolean.
- `artifact_path` — absolute path to the artifact file (str).

The lint checks for each key as a string literal in the code. The dict construction can be inline (`{"last_run": ..., ...}`) or built incrementally (`result["last_run"] = ...`). Either form passes as long as all three keys appear.

**Why:** A consumer needs three answers: when, did it work, where is the output. Missing any of the three forces log archaeology.

**Correct:**
```python
result = {
    "last_run": datetime.utcnow().isoformat() + "Z",
    "success": True,
    "artifact_path": str(artifact_path.resolve()),
}
(run_dir / "result.json").write_text(json.dumps(result, indent=2))
```

**Incorrect:**
```python
# Missing artifact_path — consumer cannot find the output
result = {"last_run": ts, "ok": True}
```

---

## Lint-is-authoritative convention

Per the `skill-frontmatter` precedent: if you find a discrepancy between this document and `scripts/observability_lint.py`, the lint wins. Update this document — do not weaken the lint to match a prose-only rule.

This applies especially to Rule D's exact key names. The lint matches `"last_run"`, `"success"`, `"artifact_path"` as fixed string literals. Renaming keys (e.g. `last_ran`, `successful`, `output_path`) breaks consumers that read the contract. If a future need demands a schema extension, add a new key alongside — never rename.

---

## Worked composed example — acme-weekly-digest

```python
import json
from datetime import datetime
from pathlib import Path

SLUG = "acme-weekly-digest"
EXT = "md"

timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
home = Path.home() / "Claude" / SLUG
run_dir = home / "runs" / timestamp
run_dir.mkdir(parents=True, exist_ok=True)

# --- do work, produce artifact ---
artifact_path = run_dir / f"artifact.{EXT}"
artifact_path.write_text(rendered_digest, encoding="utf-8")
success = True

# --- write result.json ---
result = {
    "last_run": datetime.utcnow().isoformat() + "Z",
    "success": success,
    "artifact_path": str(artifact_path.resolve()),
}
(run_dir / "result.json").write_text(json.dumps(result, indent=2))

# --- update latest.json symlink atomically ---
latest = home / "latest.json"
tmp = home / "latest.json.tmp"
if tmp.exists() or tmp.is_symlink():
    tmp.unlink()
tmp.symlink_to(run_dir / "result.json")
import os
os.replace(tmp, latest)
```

Lint verdict on this block: `passed: true`, 0 fails, 0 warns, all 4 rules satisfied.
