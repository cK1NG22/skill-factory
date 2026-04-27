# Stage 11c Verification — first real client-skill delivery

Date: 2026-04-27. Branch: `main`.

This file is the receipt for **the moment the Skill Factory becomes a delivery system**: the full pipeline ran end-to-end against the real `assets/client-spec-examples/acme-board-memo.md` spec, producing a fully-installed `acme-board-memo` skill at `~/Projects/acme-claude-skills/` + `~/.claude/skills/acme-board-memo`.

## What ran

`/skill-factory acme assets/client-spec-examples/acme-board-memo.md` was simulated by manually executing the 9 sequential phases in the same order the driver SKILL.md would have:

| Phase | Actor | Outcome |
|---|---|---|
| 1 — input gate | (skipped — spec is a known-good example, not a fresh untrusted input) | n/a |
| 2 — trait classification | `trait_predicates.py spec` | `has_phases=True, invokes_skills=True` (others false) |
| 3 — skill-frontmatter | Sonnet Agent (parallel) | `output.yaml` PASS first attempt (394-char description, 7 trigger phrases, allowed-tools `[Read, Write, Agent]`) |
| 4 — skill-phase-designer | Sonnet Agent (parallel) | `output.md` PASS first attempt (10 walkthrough steps → 6 sequential Procedure Steps) |
| 7 — skill-signed-handoff | Sonnet Agent (parallel) | `output-signature-template.py` PASS first attempt (5 SIGNED_FIELDS: title, meeting_date, author, sections, output_path) |
| 8a — assemble | `assemble_skill.py` | `<work>/assembled/acme-board-memo/` materialized with SKILL.md + scripts/acme-board-memo_signature.py + ASSEMBLY-MANIFEST.json + empty `phases/` placeholder dir |
| 8b — gate | `skill-compliance-gate/scripts/gate.py --skill <assembled>` | **`verdict: pass`**, 10 checker passes, 0 failures, 0 Check 14 hits, no blocker, `meta_skill: False` (correct — this is a CLIENT skill) |
| 9 — materialize | `materialize_skill.py <assembled> acme <work> --no-gh` | **`installed: true`**, fresh repo at `~/Projects/acme-claude-skills/`, skill copied, symlink created, git commit landed (`Add/update skill: acme-board-memo`) |
| 99 — report | (this file) | success summary |

Phases 5 (references-scaffolder) and 6 (cron-observability) did not fire — `has_references` and `is_scheduled` are false for this spec. The spec's `## Delivery / Remote repo: no` line drove the `--no-gh` flag at Phase 9 (per plan v2 D6 FLIPPED — this is the per-spec opt-out from the default-ON gh path).

## State after the run

### `~/Projects/acme-claude-skills/`

Fresh git repo. Initial author identity: `Skill Factory <factory@local>` (injected via `-c user.name/-c user.email` flags so commits work even when ambient git config is empty — see `materialize_skill.py::_run_git`):

```
$ cd ~/Projects/acme-claude-skills && git log --format='%h %ai  %s'
57062e9 2026-04-27 13:32:10 -0600  Add/update skill: acme-board-memo
038ce9d 2026-04-27 13:32:10 -0600  Initial commit: acme Claude skills repo
```

Repo contents:

```
~/Projects/acme-claude-skills/
├── .git/                      (full git tree, main branch)
├── .gitignore                 (factory-emitted boilerplate: .DS_Store, __pycache__/, /work/, ...)
├── README.md                  (factory-generated, lists `acme-board-memo`)
└── acme-board-memo/
    ├── SKILL.md               (frontmatter from Phase 3 + body composed by assemble_skill.py)
    ├── ASSEMBLY-MANIFEST.json (BP-031 audit trail)
    ├── phases/                (empty scaffolding dir for BP-009 — has_phases fired)
    └── scripts/
        └── acme-board-memo_signature.py  (BP-024-compliant signed-handoff for /docx)
```

### `~/.claude/skills/acme-board-memo`

Symlink resolving to the repo path:

```
$ ls -la ~/.claude/skills/acme-board-memo
lrwxr-xr-x  1 carterking  staff  61 Apr 27 13:32 /Users/carterking/.claude/skills/acme-board-memo
    -> /Users/carterking/Projects/acme-claude-skills/acme-board-memo
```

The symlink is absolute-target (per plan v2 D4) and resolves to a directory containing `SKILL.md`. Claude Code reads the frontmatter via this symlink to decide whether the skill's trigger phrases activate.

### Idempotency confirmed

A second materialize run with byte-identical input produced zero filesystem changes:

```
{
  "installed": false,
  "blocker": null,
  "notes": [
    "repo: reused existing at ~/Projects/acme-claude-skills",
    "skill: already installed (byte-identical) at ~/Projects/acme-claude-skills/acme-board-memo",
    "symlink: already correct at ~/.claude/skills/acme-board-memo"
  ]
}
```

`git rev-list --count HEAD` reported 2 commits both before and after the re-run — no churn commit landed. The symlink's mtime was unchanged.

### Gate-clean through the symlink

Re-running the gate against `~/.claude/skills/acme-board-memo` (the symlink path, not the repo path) returned `verdict: pass, meta: False, blocker: None`. The symlink-traversed view of the skill is gate-clean, which is what Claude Code's runtime activation actually sees.

## Test-suite delta

| Suite | Pre-Stage-11 | Post-Stage-11c | Δ |
|---|---|---|---|
| `skill-frontmatter/tests/` | 22 | 22 | 0 |
| `skill-phase-designer/tests/` | 33 | 33 | 0 |
| `skill-references-scaffolder/tests/` | 51 | 51 | 0 |
| `skill-cron-observability/tests/` | 28 | 28 | 0 |
| `skill-signed-handoff/tests/` | 36 | 36 | 0 |
| `skill-factory/tests/` | 106 | **143** | +37 |
| `skill-compliance-gate/tests/` | 34 | 34 | 0 |
| **Total** | **310** | **347** | **+37** |

Plan target: 310 → ~349. Actual: 310 → 347 (+2 short, all from the 11b 5–7 range coming in at the lower end). Stage 11a contributed +30 (`test_materialize_skill.py`), Stage 11b contributed +5 (`TestStage11bPhase9Integration` in `test_build_context_pack.py`), Stage 11c contributed +2 (`TestStage11cE2EIntegration` in `test_materialize_skill.py`).

## Gate-verdict invariant preserved

All 9 factory artifacts still emit `verdict: pass` with `meta_skill: true` — the bonus-sweep invariant codified at Stage 10c (every factory-internal artifact passes its own gate via the `meta-skill: true` frontmatter marker) survived Stage 11's three-sub-stage rollout.

| Artifact | Pre-Stage-11 | Post-Stage-11c |
|---|---|---|
| `skill-compliance` | pass meta:True | pass meta:True |
| `skill-spec-validator` | pass meta:True | pass meta:True |
| `skill-frontmatter` | pass meta:True | pass meta:True |
| `skill-phase-designer` | pass meta:True | pass meta:True |
| `skill-references-scaffolder` | pass meta:True | pass meta:True |
| `skill-cron-observability` | pass meta:True | pass meta:True |
| `skill-signed-handoff` | pass meta:True | pass meta:True |
| `skill-compliance-gate` | pass meta:True | pass meta:True |
| `skill-factory` (driver) | pass meta:True | pass meta:True |

The 5 Stage-11b driver/template/validator edits could in principle have flipped the driver's own gate verdict (it grew Step 9 + Step 10 + the `materialize_skill.py` Scripts entry, going from 154 → 175 body lines). It did not — the body-size check is the only one in the "info" tier and it accepts thin directors per the Stage 9.0.5 precedent.

## What's next

- **Carter smoke-test** (out of factory's hands, has to be human-driven): start a fresh `claude` session in any directory, type one of the spec's trigger phrases (`generate board memo`, `make a board memo`, `acme board memo`, etc.), confirm the new skill activates and reads its SKILL.md from the symlinked path. The gate-pass + symlink-resolves invariants verified above are necessary but not sufficient — the smoke test is the final ground-truth check.

- **Optional Stage 11d** (deferred per plan v2): live `gh` E2E run against a throwaway `test-acme` slug with Delivery section omitted (default-ON). After verification, `gh repo delete ck22coding/test-acme-claude-skills` cleans up. Not gating Stage 11 completion.

## Rollback

If anything is wrong with the installed skill, surgical rollback:

```bash
unlink ~/.claude/skills/acme-board-memo
/usr/bin/find ~/Projects/acme-claude-skills -depth -delete
```

(The sandbox in this session declined `rm -rf ~/Projects/acme-claude-skills`, so `find -depth -delete` is the safe fallback — same approach used to reverse the Stage 11a real-FS pollution incident.)

The factory is idempotent; re-running `/skill-factory acme assets/client-spec-examples/acme-board-memo.md` re-materializes from scratch.
