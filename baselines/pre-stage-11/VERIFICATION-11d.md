# Stage 11d Verification — live `gh` path E2E (throwaway test-acme)

Date: 2026-04-27. Branch: `main`. **Status: GREEN.** No source changes.

This file is the receipt for plan v2 §"Optional Stage 11d (deferred, document only) — live `gh` E2E". Stage 11c deliberately ran with `--no-gh` to keep the GitHub-creation path off the critical path of initial bring-up. Stage 11d closes that gap by exercising the default-ON `gh` path against a throwaway `test-acme` slug and verifying every materializer-side claim against the live GitHub API.

## Pre-flight

| Check | Outcome |
|---|---|
| `gh auth status` | ✓ ck22coding authed; scopes `gist read:org repo workflow` |
| `~/Projects/test-acme-claude-skills` absent | ✓ `No such file or directory` |
| `~/.claude/skills/test-acme-board-memo` absent | ✓ no symlink, no real entry |
| `gh repo view ck22coding/test-acme-claude-skills` | ✓ 404 (`Could not resolve to a Repository`) |

## What ran

The Stage 11d goal is the **`gh` path of `materialize_skill.py`** specifically (Stage 11c already proved Phases 1–8). Executing the full driver pipeline again would re-validate work already verified in 11c at significant token cost without exercising new code paths. So 11d focuses on the new code paths:

1. **Spec-decision logic** (where the no-Delivery → gh-ON decision lives): authored a no-Delivery spec at `/tmp/skill-factory-stage-11d/spec/client-spec.md` (a trimmed `test-acme-board-memo` spec) and ran `parse_delivery_section()` against it as a Python sanity check. Verdict: `{"present": False, "remote_repo": None}` → director would NOT pass `--no-gh` → gh path fires by default.
2. **Materializer gh execution path**: cloned the Stage 11c assembled artifact at `~/Projects/acme-claude-skills/acme-board-memo/` to `/tmp/skill-factory-stage-11d/assembled/test-acme-board-memo/`, renamed `name:` in `SKILL.md` frontmatter from `acme-board-memo` to `test-acme-board-memo` (otherwise the symlink path would collide with the existing 11c install), updated `ASSEMBLY-MANIFEST.json` `slug` + `scripts` accordingly, and renamed `scripts/<old>_signature.py` to `scripts/test-acme-board-memo_signature.py`. Then invoked:

   ```
   python3 skill-factory/scripts/materialize_skill.py \
       /tmp/skill-factory-stage-11d/assembled/test-acme-board-memo \
       test-acme \
       /tmp/skill-factory-stage-11d
   ```

   No `--no-gh`, no `--force`. Default-ON gh path engaged.

## Materializer verdict (first attempt, no retries)

```
{
  "blocker": null,
  "gh_url": "https://github.com/ck22coding/test-acme-claude-skills",
  "installed": true,
  "notes": [
    "repo: initialized fresh at /Users/carterking/Projects/test-acme-claude-skills",
    "skill: copied to /Users/carterking/Projects/test-acme-claude-skills/test-acme-board-memo",
    "symlink: created → /Users/carterking/Projects/test-acme-claude-skills/test-acme-board-memo at /Users/carterking/.claude/skills/test-acme-board-memo",
    "git: committed skill `test-acme-board-memo` to /Users/carterking/Projects/test-acme-claude-skills",
    "gh: created private remote at https://github.com/ck22coding/test-acme-claude-skills",
    "gh: collaborator adamkingai present (push permission)"
  ],
  "repo_path": "/Users/carterking/Projects/test-acme-claude-skills",
  "skill_path": "/Users/carterking/Projects/test-acme-claude-skills/test-acme-board-memo",
  "skipped": null,
  "symlink_path": "/Users/carterking/.claude/skills/test-acme-board-memo"
}
```

Exit code 0.

## Independent live-GitHub verification

Each materializer claim cross-checked against `gh` / `gh api` (NOT trusting the script's own notes blindly):

| Claim | Verification | Result |
|---|---|---|
| Repo created PRIVATE | `gh repo view ck22coding/test-acme-claude-skills --json visibility,createdAt,defaultBranchRef,pushedAt,url` | ✓ `visibility: PRIVATE`, `createdAt: 2026-04-27T19:47:29Z`, `defaultBranchRef.name: main`, `pushedAt: 2026-04-27T19:47:31Z` |
| Initial commit landed on remote | `gh api repos/ck22coding/test-acme-claude-skills/commits` | ✓ `4b43b20 Initial commit: test-acme Claude skills repo` (author `Skill Factory`) and `2382fac Add/update skill: test-acme-board-memo` (author `Skill Factory`) — both SHAs match local `git log` |
| `adamkingai` collaborator-add succeeded | `gh api repos/ck22coding/test-acme-claude-skills/invitations` | ✓ pending invite id `316494744`, invitee `adamkingai`, inviter `ck22coding`, `permissions: "write"`, `created_at: 2026-04-27T19:47:32Z`, `expired: false` |
| Origin remote wired | `git -C ~/Projects/test-acme-claude-skills remote -v` | ✓ `origin https://github.com/ck22coding/test-acme-claude-skills.git` (fetch + push) |
| Symlink resolves correctly | `ls -l ~/.claude/skills/test-acme-board-memo` | ✓ `-> /Users/carterking/Projects/test-acme-claude-skills/test-acme-board-memo` (absolute target per plan v2 D4) |
| SKILL.md reachable through symlink | `head -3 ~/.claude/skills/test-acme-board-memo/SKILL.md` | ✓ `name: test-acme-board-memo` in frontmatter |

## Pending-invite nuance

`gh api repos/.../collaborators` returned **only** the owner (ck22coding with admin). On a personal-account repo, an invitee does not appear under `/collaborators` until they accept the invite — they live in `/invitations` instead. This is normal GitHub behavior, not a materializer bug.

The materializer's note string `"gh: collaborator adamkingai present (push permission)"` is technically optimistic — it should read something like `"gh: invited adamkingai (push permission, pending acceptance)"`. Captured as a non-blocking polish for a future stage; does not affect functional correctness, since `gh api ... /collaborators -X PUT` returned 201 Created (the invite was successfully sent — that's what the materializer was asserting).

## Cleanup state

Partial cleanup. Carter to finish manually:

| Step | Status |
|---|---|
| `~/.claude/skills/test-acme-board-memo` symlink | ✓ removed via `unlink` |
| `~/Projects/test-acme-claude-skills/` local repo | ⚠️ exists — sandbox declined `rm -rf`; deferred to Carter |
| `ck22coding/test-acme-claude-skills` GitHub remote | ⚠️ exists — `gh repo delete --yes` failed with `HTTP 403: Must have admin rights ... needs the "delete_repo" scope`. Token has `repo` (sufficient for create) but not `delete_repo` (needed for delete). Carter to delete via GitHub UI (https://github.com/ck22coding/test-acme-claude-skills/settings → Danger Zone) OR run `gh auth refresh -h github.com -s delete_repo` to grant the scope and retry. |
| `/tmp/skill-factory-stage-11d/` tmpfs work tree | left in place (cheap; macOS `/private/tmp` clears on reboot) |

## Test-suite delta

**None.** Stage 11d is verification-only. No source changes, no new tests, no regressions:

| Suite | Pre-Stage-11d | Post-Stage-11d | Δ |
|---|---|---|---|
| (all 7 suites) | 347 | 347 | 0 |

## Auth-scope finding (action item, non-blocking)

The factory invokes:
- `gh auth status` (any auth)
- `gh repo view <owner>/<repo>` (covered by `repo`)
- `gh repo create --private <repo>` (covered by `repo`)
- `gh api repos/.../collaborators/<user> -X PUT -f permission=push` (covered by `repo`)

But the **post-test cleanup** step in 11d's design (`gh repo delete`) requires `delete_repo` — a scope the factory's normal flow never needs, since deletes are always exceptional manual operations. For future automated 11d-style throwaway runs, the operator's gh token must have `delete_repo` granted explicitly. Worth documenting in a Stage 11 readme if this verification is ever automated.

## Invariant table (Stage 11d invariants from plan v2)

| Invariant | Status |
|---|---|
| `gh auth status` passes before factory starts | ✓ |
| Default-ON `gh` fires when spec lacks `## Delivery / Remote repo: no` | ✓ (parser confirmed `present=False`; materializer engaged gh path with no `--no-gh`) |
| `gh repo create --private` succeeds | ✓ (PRIVATE confirmed via `gh repo view`) |
| Initial commit pushes to `ck22coding/<company>-claude-skills` | ✓ (SHAs match between local + remote) |
| `adamkingai` collaborator-add succeeds (invite sent) | ✓ (pending invite #316494744 with write permission) |

**All five Stage 11d invariants GREEN, first attempt.**

## What's next

- **Carter manual cleanup** — delete remote + local repo (paths above).
- **Carter smoke-test of `acme-board-memo`** still pending (Stage 11c follow-through; orthogonal to 11d).
- **Materializer note-string polish** (optional) — change `"gh: collaborator <name> present"` to `"gh: invited <name> (pending acceptance)"` for accuracy. Captured here; not stage-gating.
- **Stage 11 wave fully complete.** No blockers; alternative next-actions live in `handoff-skill-factory.md`.
