# `materialize_skill.py` contract

Phase-scoped reference for Phase 9 (the per-client repo + symlink
install + opt-in `gh` step). Cited by `../director.md` Steps A, C, D.

## Verdict dict schema

`materialize()` returns a `MaterializeResult` dataclass; the CLI prints
its `to_dict()` form to stdout. Schema:

```json
{
  "installed": true,
  "skipped": null,
  "blocker": null,
  "repo_path": "/Users/.../Projects/<company>-claude-skills",
  "skill_path": "/Users/.../Projects/<company>-claude-skills/<slug>",
  "symlink_path": "/Users/.../.claude/skills/<slug>",
  "gh_url": "https://github.com/ck22coding/<company>-claude-skills",
  "notes": [
    "repo: initialized fresh at <repo_path>",
    "skill: copied to <skill_path>",
    "symlink: created → <skill_path> at <symlink_path>",
    "git: committed skill `<slug>` to <repo_path>",
    "gh: created private remote at <gh_url>",
    "gh: collaborator adamkingai present (push permission)"
  ]
}
```

| Field | Type | Meaning |
|---|---|---|
| `installed` | bool | True iff at least one filesystem change happened (repo init, skill copy, symlink create, gh repo create, or new commit). |
| `skipped` | str \| null | `"meta"` when Phase 9 short-circuited on the `meta-skill: true` marker; otherwise null. |
| `blocker` | str \| null | One-line description of the failure that BLOCKERed the run; null on success / no-op. |
| `repo_path` | str \| null | Absolute path to `~/Projects/<company>-claude-skills/`. Null only on meta-skill skip. |
| `skill_path` | str \| null | Absolute path to `~/Projects/<company>-claude-skills/<slug>/`. Null only on meta-skill skip. |
| `symlink_path` | str \| null | Absolute path to `~/.claude/skills/<slug>/`. Null only on meta-skill skip. |
| `gh_url` | str \| null | GitHub URL when `gh` ran successfully; null otherwise. |
| `notes` | list[str] | Human-readable status log appended in declaration order. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success, idempotent no-op, or meta-skill skip. `blocker` is null. |
| 1 | BLOCKER. `blocker` is set; the verdict still printed to stdout for inspection. |
| 2 | Bad usage (missing assembled dir, missing args, malformed frontmatter). Driver bug, not user-resolvable. |

The Phase 9 director maps exit 1 to the canonical BLOCKER line per
BP-028 and STOPs before Phase 99. Exit 2 is treated as a separate
driver-bug BLOCKER.

## Idempotency rules

The materializer is safe to re-run. Per plan v2 D5:

| State | Behavior |
|---|---|
| Repo missing | Create (`git init -b main`, `.gitignore`, `README.md`, initial commit). |
| Repo exists, is a git repo | Reuse — append the new skill, update `README.md`, single new commit per run. |
| Repo exists, NOT a git repo | BLOCKER. User chooses: `git init` (bless as factory-managed) or move aside. |
| Skill dir missing | Copy from assembled tree. |
| Skill dir exists, byte-identical | No-op. `installed: false`, `notes` records "already installed (byte-identical)". |
| Skill dir exists, different content | BLOCKER. `--force` does NOT bypass. User bumps slug or `rm -rf` first. |
| Symlink missing | Create. |
| Symlink correct | No-op. |
| Symlink wrong target | BLOCKER without `--force`. With `--force`, replaced (cheap to redo); old target logged in `notes`. |
| Real entry at symlink path | BLOCKER without `--force`. With `--force`, real entry unlinked and replaced; logged in `notes` for audit. |

Byte-identity is verified via recursive `filecmp.dircmp` walk that
skips `.git/` (the per-client repo's `.git` is irrelevant to skill
content equivalence).

## `--force` flag scope

`--force` ONLY replaces SYMLINKS at `~/.claude/skills/<slug>/`. It
NEVER overwrites the skill directory at
`~/Projects/<company>-claude-skills/<slug>/`. Committed code is sacred
(plan v2 D5 + Q5). The factory's standard run never sets `--force` —
it's reserved for manual reruns by the user when a symlink is being
intentionally redirected.

## Meta-skill exception

When the assembled skill carries `meta-skill: true` in frontmatter (per
BP-003 exception, Stage 10c), Phase 9 returns early with
`skipped: "meta"` and touches no filesystem.

The 9 factory artifacts marked `meta-skill: true`:

- `skill-compliance`
- `skill-spec-validator`
- `skill-frontmatter`
- `skill-phase-designer`
- `skill-references-scaffolder`
- `skill-cron-observability`
- `skill-signed-handoff`
- `skill-compliance-gate`
- `skill-factory` (the driver itself)

These already live at `~/Projects/skill-factory/`, the source-of-truth
repo. They must NOT be installed under
`~/Projects/skill-factory-claude-skills/` (that path doesn't exist and
shouldn't be created — the meta-skill exception prevents the
recursive-name confusion that surfaced during Stage 9c self-bootstrap).

The detection helper is `materialize_skill.is_meta_skill(path)`, which
mirrors `skill-compliance-gate/scripts/gate.py::is_meta_skill`. False
on missing SKILL.md, missing frontmatter, no marker, or any other
read error.

## Why materialization is inline (not a sub-skill)

Per plan v2 D1 (parallel to Stage 10 D3 for `assemble_skill.py`):
materialization is purely deterministic (mkdir, copy, `ln -s`,
subprocess). There are no judgment calls a Sonnet Agent would add value
to. Inline scripts are the right shape for deterministic mechanics;
sub-skills are the right shape for tasks needing an LLM in the loop
(frontmatter authoring, phase decomposition, observability snippet
generation).

Keeping it inline also avoids polluting `~/.claude/skills/` with a
"just for the factory" sub-skill and keeps the sub-skill count stable
at 9 (unchanged from Stage 10c).
