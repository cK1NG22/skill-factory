# Instrumentation snippet — acme-weekly-digest

Target skill: `acme-weekly-digest`. Artifact extension: `.md`. Cron frequency: `0 16 * * 5`.

Paste the following Python block into the skill's cron orchestration, wrapping the existing "produce artifact" logic. All four BP-022 rules (A, B, C, D) are satisfied.

```python
import json
import os
from datetime import datetime
from pathlib import Path

SLUG = "acme-weekly-digest"
EXT = "md"

timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
home = Path.home() / "Claude" / SLUG
run_dir = home / "runs" / timestamp
run_dir.mkdir(parents=True, exist_ok=True)

# --- Produce artifact ---
# (Replace the next two lines with the skill's real work)
rendered_digest = "# Weekly digest\n\n(content here)\n"
artifact_path = run_dir / f"artifact.{EXT}"
artifact_path.write_text(rendered_digest, encoding="utf-8")
success = True

# --- Write result.json ---
result = {
    "last_run": datetime.utcnow().isoformat() + "Z",
    "success": success,
    "artifact_path": str(artifact_path.resolve()),
}
(run_dir / "result.json").write_text(json.dumps(result, indent=2))

# --- Update latest.json symlink atomically ---
latest = home / "latest.json"
tmp = home / "latest.json.tmp"
if tmp.exists() or tmp.is_symlink():
    tmp.unlink()
tmp.symlink_to(run_dir / "result.json")
os.replace(tmp, latest)
```

## Rationale

- **Rule A** — `result.json` is written under `~/Claude/acme-weekly-digest/runs/<timestamp>/`, with the timestamp computed via `datetime.utcnow().strftime(...)`.
- **Rule B** — the artifact is written to `run_dir / f"artifact.{EXT}"` (a `.md` file) in the same directory as `result.json`.
- **Rule C** — `latest.json` is maintained as a symlink at the skill root, atomically swapped via `os.replace`.
- **Rule D** — `result.json` includes `last_run` (ISO-8601), `success` (bool), `artifact_path` (str).
