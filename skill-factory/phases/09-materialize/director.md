# Phase 9 — materialize (always fires except for meta-skills)

Phase 9 closes the install loop and the version-control loop. After Phase
8's gate emits PASS, the assembled skill at `<work>/assembled/<slug>/` is
proven compliant — but it is unreachable from `~/.claude/skills/` (so
Claude Code never activates it) and lives only in the factory's scratch
dir (so it is lost on the next `rm -rf ~/Claude/skill-factory/`). Phase
9 fixes both.

Phase 9 does four things, in order:

1. **Detect meta-skill.** When the assembled skill carries
   `meta-skill: true` in frontmatter (per BP-003 exception, plan v2 D7),
   short-circuit. Meta-skills already live at `~/Projects/skill-factory/`.
2. **Determine `gh` mode.** Parse the optional `## Delivery / Remote repo`
   field from the input spec. Default per plan v2 D6 (FLIPPED) is `gh` ON;
   `Remote repo: no` is the per-spec opt-out.
3. **Materialize.** Run `materialize_skill.py` to create / extend the
   per-client repo at `~/Projects/<company>-claude-skills/`, copy the
   skill, symlink it into `~/.claude/skills/<slug>/`, and (when `gh` is
   on) `gh repo create --private` + add `adamkingai` as collaborator.
4. **Interpret the verdict + STOP-on-BLOCKER.**

On a clean materialize, Phase 99 (report) fires. On any BLOCKER, the
director STOPs before Phase 99 per BP-028 — the BLOCKER line in
`notes.md` names what conflicts (e.g., wrong-target symlink, conflicting
skill dir, gh auth failure).

## Procedure

### Step A — Detect meta-skill marker

Inspect the assembled skill's frontmatter for the `meta-skill: true`
marker. The materialize script provides a Python helper:

```bash
python3 -c "
import sys
sys.path.insert(0, '~/Projects/skill-factory/skill-factory/scripts')
import materialize_skill as ms
from pathlib import Path
print('meta' if ms.is_meta_skill(Path('<work>/assembled/<slug>')) else 'client')
"
```

If the output is `meta`, write
`SKIPPED: meta-skill — Phase 9 short-circuited per plan v2 D7` to
`<work>/phases/09-materialize/notes.md` and continue to Step 10
(Phase 99 — report). The report should announce
`materialize: SKIPPED (meta-skill)`.

If the output is `client`, continue to Step B.

See `references/materialization-contract.md` §"Meta-skill exception" for
the full rationale and the list of all 9 marker'd factory artifacts.

### Step B — Determine `gh` mode from the spec's Delivery section

Parse the spec's optional `## Delivery` section. The materialize script
provides a parser:

```bash
python3 -c "
import sys
sys.path.insert(0, '~/Projects/skill-factory/skill-factory/scripts')
import materialize_skill as ms
from pathlib import Path
result = ms.parse_delivery_section(Path('<spec-path>'))
print('no-gh' if result['remote_repo'] == 'no' else 'gh')
"
```

Per plan v2 D6 (FLIPPED), `gh` is ON by default. The flag flips to OFF
only when the spec's Delivery section explicitly contains
`Remote repo: no`. Treat all other cases (section missing, section
present without `Remote repo` line, `Remote repo: yes`) as `gh` ON.

See `references/gh-cli-invocation.md` for the full `gh` decision matrix
and the auth / repo-view / collaborator-add chain.

### Step C — Run `materialize_skill.py`

Invoke the materializer with the assembled path, the company slug
(known from the driver invocation `/skill-factory <company> <spec>`),
and the optional flags from Steps A–B:

```bash
python3 ~/Projects/skill-factory/skill-factory/scripts/materialize_skill.py \
    <work>/assembled/<slug> <company> <work> [--no-gh]
```

The third positional arg (`<work>`) is reserved for future spec lookup
(parse_delivery_section is called from Step B above; Stage 11b does not
yet wire it through the script's CLI). Pass `--no-gh` only when Step B
returned `no-gh`. **Never pass `--force`** — `--force` is reserved for
manual reruns by the user when a symlink is intentionally being
replaced; the factory's standard run never sets it.

Exit codes (per `references/materialization-contract.md`):

- 0 → success or idempotent no-op. Continue to Step D.
- 1 → BLOCKER. Continue to Step D (it interprets the verdict).
- 2 → bad usage / missing assembled dir. This is a driver bug, not a
  user-resolvable condition. Write
  `BLOCKER: materialize_skill.py exited 2 — <stderr>` to
  `<work>/notes.md` and STOP.

The script prints a verdict JSON to stdout regardless of exit code —
capture it for Step D.

### Step D — Interpret the verdict and STOP-on-BLOCKER

Parse the verdict JSON printed by Step C. The schema is documented in
`references/materialization-contract.md` §"Verdict dict schema."

Branch on the `blocker` field:

- **`blocker: null`** AND `skipped: null` → real install happened. Read
  `installed`, `repo_path`, `skill_path`, `symlink_path`, and
  (when `gh` was on) `gh_url`. Append the verdict's `notes` to
  `<work>/phases/09-materialize/output.md` (the per-phase result file).
  Continue to Step 10 (Phase 99 — report).
- **`blocker: null`** AND `skipped: "meta"` → already handled by Step A's
  short-circuit; this branch is defensive. Continue to Step 10.
- **`blocker: "<message>"`** → copy the canonical BLOCKER line verbatim
  to `<work>/notes.md` and STOP. Do NOT enter Phase 99. The user
  resolves manually (per the BLOCKER text — usually `unlink` a stale
  symlink, `rm -rf` a stale skill dir, or `gh auth login`) and re-runs
  the factory.

Canonical BLOCKER format:

```
BLOCKER: materialize failed — <verdict.blocker text verbatim>
```

Do NOT reformat. The materializer's blocker text already names the
specific path and remediation; reformatting hides debugging signal.

## What this phase does NOT do

- Does NOT run `git push` against any remote that isn't set up by
  `gh repo create`. When `gh` is OFF, the local repo has no remote and
  the user adds one manually if they want to push later.
- Does NOT auto-fix conflicts. A pre-existing skill dir with different
  content BLOCKERs unconditionally; `--force` does NOT bypass per
  plan v2 D5 (committed code is sacred). Symlink conflicts BLOCKER
  without `--force` and only the user invokes `--force` manually.
- Does NOT push to `main` of the per-client repo on every run. The
  initial `gh repo create --push` populates `main`; subsequent runs
  commit locally and the user pushes when ready (out of scope for
  Stage 11; could be a Stage 12 add).
- Does NOT support cross-company skills. Each `/skill-factory` run
  produces one skill bound to one company. Multi-company batching is
  Stage 12+ ergonomics.

## Cross-reference

- Verdict dict schema, idempotency rules, BLOCKER conditions:
  `references/materialization-contract.md`.
- `gh` decision matrix, auth chain, collaborator-add semantics:
  `references/gh-cli-invocation.md`.
- BP-003 meta-skill exception (the `meta-skill: true` marker rule):
  `../../../patterns/meta/bp-003-name-rules.md` §"Meta-skill exception
  (Stage 10c)".
- BLOCKER convention on materialize FAIL (BP-028): the materializer
  emits the canonical BLOCKER line; the driver STOPs.
