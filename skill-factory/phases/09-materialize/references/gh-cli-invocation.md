# `gh` CLI invocation contract

Phase-scoped reference for Phase 9's GitHub-creation step. Cited by
`../director.md` Step B.

## When `gh` runs

Per plan v2 D6 (FLIPPED from v1's opt-in default):

| Spec's `## Delivery / Remote repo` field | `gh` mode |
|---|---|
| Section absent | ON (default) |
| `Remote repo: yes` | ON |
| `Remote repo: no` | OFF (`--no-gh` passed to materializer) |
| Section present, no `Remote repo` line | ON (default) |

The default-ON choice (v1 → v2 flip) reflects the steady-state
expectation: the vast majority of factory runs are real client
deliveries that should land on GitHub for collaboration with Adam (per
D10). The escape hatch (`Remote repo: no`) is for development iteration
+ smoke-test runs + specs that should never publish (internal-only
POCs).

Stage 11c's first real client-skill delivery uses `Remote repo: no` to
keep the GitHub-creation path off the critical path of initial
bring-up. Stage 11d (deferred) covers the live-with-`gh` E2E.

## What `gh` does (when ON)

The materializer runs four `gh` subprocess calls in order. Each is
a thin wrapper around a single `subprocess.run` invocation — that
seam is what tests intercept via `unittest.mock.patch`.

### 1. `gh auth status`

Verifies the local `gh` install is authenticated. Failure modes:

- `gh` not installed (`FileNotFoundError`) → BLOCKER with remediation
  `brew install gh`.
- Auth expired or never run → BLOCKER with remediation `gh auth login`.

The materializer never silently falls back to local-only when `gh` is
ON. A user who opted in to `gh` and hit an auth wall wants to fix it,
not silently get a local-only repo.

### 2. `gh repo view ck22coding/<company>-claude-skills`

Checks whether the remote already exists. Idempotency hinge:

- Exists, owned by `ck22coding` → reuse (don't re-create); skip step 3.
- Exists, owned by someone else → BLOCKER. Manual resolution; the
  factory will not push to a remote it doesn't own.
- Missing → continue to step 3.

The repo URL recovered from this call is also what populates
`verdict.gh_url` after a successful run.

### 3. `gh repo create ck22coding/<company>-claude-skills --private --source=<repo_path> --push`

Creates the remote repo, attaches the local repo at `<repo_path>` as
its source, and pushes the initial commit. Always `--private` per
plan v2 D11.

If the user later needs to publish (e.g., open-source the per-client
skills), they flip visibility manually via `gh repo edit --visibility
public`. The factory does not auto-publish.

Failure modes:

- Network unavailable / rate-limited / GitHub down → BLOCKER with raw
  `gh` stderr captured in the verdict's `notes`.
- Repo creation succeeds but push fails (e.g., empty initial commit
  rejected) → BLOCKER. Manual cleanup needed (`gh repo delete` then
  re-run the factory).

### 4. `gh api -X PUT repos/ck22coding/<company>-claude-skills/collaborators/adamkingai -f permission=push`

Adds Adam as a push-permission collaborator on every newly-created
repo (per plan v2 D10).

Idempotency: the API returns 204 (no content) when the user is already
a collaborator. Older `gh` versions sometimes return nonzero for the
already-collaborator case; the materializer's helper checks stderr for
`already` or `204` strings to handle both.

This step is **non-fatal** if it fails — the factory logs a WARN to
`notes` rather than BLOCKERing. Rationale: the repo + skill are already
in place; Adam can be added manually via the GitHub UI if the API call
flaked. A BLOCKER here would force re-running the entire factory just
to retry an idempotent API call.

## Decision matrix (Step B output → CLI args)

| Step A result | Step B result | materialize_skill.py CLI args |
|---|---|---|
| meta | (skipped) | (Phase 9 short-circuits) |
| client | `gh` | `<assembled> <company> <work>` (no extra flags) |
| client | `no-gh` | `<assembled> <company> <work> --no-gh` |

The materializer's Python API uses `gh: bool = True` by default,
matching the CLI's "default ON" behavior. Production callers (this
phase director) determine the boolean from the spec. Unit tests pass
`gh=False` explicitly via the kwarg seam to avoid hitting GitHub.

## Why the `gh` calls live in `materialize_skill.py`, not the director

Plan v2 D1: deterministic mechanics belong in inline scripts, not as
sub-skill Agent spawns. Each `gh` call is `subprocess.run` of a fixed
argv — there's no LLM judgment involved in choosing the right command,
parsing output, or deciding next steps. Wrapping these in a sub-skill
would add Agent-spawn overhead (context copy + serialization) without
buying any quality.

The director's job is to wire spec intent → flag, then read the
verdict back. Everything between is mechanical.
