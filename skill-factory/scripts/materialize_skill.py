#!/usr/bin/env python3
"""
materialize_skill.py — Phase 9 of the Skill Factory.

Reads a gate-passing assembled skill from `<work>/assembled/<slug>/` and
installs it into the user's ecosystem:

  1. Materializes (or re-uses) a per-client git repo at
     `~/Projects/<company>-claude-skills/`.
  2. Copies the skill directory into the repo at
     `~/Projects/<company>-claude-skills/<slug>/`.
  3. Symlinks `~/.claude/skills/<slug>/` → the repo path so Claude Code
     activates the skill.
  4. (When `gh=True` / `--no-gh` not set) creates a private GitHub repo
     at `ck22coding/<company>-claude-skills` via the `gh` CLI and adds
     `adamkingai` as a collaborator (per plan v2 D6 + D10 + D11).

Idempotency (plan v2 D5):
  - Repo missing → create.
  - Repo exists → reuse, append the new skill.
  - Skill dir exists with byte-identical content → no-op.
  - Skill dir exists with different content → BLOCKER. `--force` does NOT
    bypass — committed code is sacred.
  - Symlink missing → create.
  - Symlink correct → no-op.
  - Symlink wrong target / real entry at that name → BLOCKER. `--force`
    DOES bypass for symlinks only (symlinks are cheap to redo).

Meta-skill skip (plan v2 D7):
  - When the assembled skill carries `meta-skill: true` in frontmatter,
    Phase 9 SHORT-CIRCUITS. Meta-skills (factory-internal) live at
    `~/Projects/skill-factory/`, not `~/Projects/<slug>-claude-skills/`.

Exit codes:
  0 — success, idempotent no-op, or meta-skill skip.
  1 — BLOCKER (failure that the user must resolve).
  2 — bad usage (missing args, missing assembled dir, etc).
"""
from __future__ import annotations

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

GH_OWNER = "ck22coding"
GH_COLLABORATOR = "adamkingai"
DEFAULT_PROJECTS_ROOT = Path("~/Projects").expanduser()
DEFAULT_SKILLS_REGISTRY = Path("~/.claude/skills").expanduser()

_FRONTMATTER_NAME_RE = re.compile(
    r"^\s*name\s*:\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE
)
_META_SKILL_RE = re.compile(
    r"^\s*meta-skill\s*:\s*true\s*$", re.MULTILINE | re.IGNORECASE
)
_DELIVERY_HEADING_RE = re.compile(r"^##\s+Delivery\s*$", re.MULTILINE)
_REMOTE_REPO_RE = re.compile(
    r"^\s*Remote\s+repo\s*:\s*(yes|no)\s*$", re.MULTILINE | re.IGNORECASE
)


@dataclass
class MaterializeResult:
    """Verdict of a materialize() run.

    `installed` is True when at least one filesystem change happened
    (repo init, skill copy, symlink create, gh repo create). `skipped`
    is "meta" when the meta-skill short-circuit fired, else None.
    `blocker` is None on success or a one-line explanation on BLOCKER.
    `gh_url` is set only when the gh path completed successfully.
    `notes` is the human-readable status log appended in declaration order.
    """

    installed: bool
    repo_path: Path | None
    skill_path: Path | None
    symlink_path: Path | None
    gh_url: str | None = None
    skipped: str | None = None
    blocker: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "installed": self.installed,
            "repo_path": str(self.repo_path) if self.repo_path else None,
            "skill_path": str(self.skill_path) if self.skill_path else None,
            "symlink_path": (
                str(self.symlink_path) if self.symlink_path else None
            ),
            "gh_url": self.gh_url,
            "skipped": self.skipped,
            "blocker": self.blocker,
            "notes": list(self.notes),
        }


class MaterializeError(Exception):
    """Raised on bad usage (exit 2). Idempotent no-ops and BLOCKERs return
    a normal MaterializeResult with `blocker` set instead of raising —
    this exception is reserved for caller errors (missing files, bad
    arguments, malformed frontmatter)."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------
# Frontmatter helpers — duplicate the gate's slim parser rather than import,
# so this script stays standalone (no skill-compliance-gate dependency at
# import time, only at runtime via the gate's verdict feeding into Phase 8).
# --------------------------------------------------------------------------

def _read_frontmatter(skill_path: Path) -> str | None:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return None
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[3:end]


def is_meta_skill(assembled_path: Path) -> bool:
    """Detect the BP-003 meta-skill exception via frontmatter (plan v2 D7).

    Mirrors `skill-compliance-gate/scripts/gate.py::is_meta_skill`. False on
    missing SKILL.md, missing/malformed frontmatter, or no marker.
    """
    fm = _read_frontmatter(assembled_path)
    if fm is None:
        return False
    return bool(_META_SKILL_RE.search(fm))


def _extract_slug(assembled_path: Path) -> str:
    fm = _read_frontmatter(assembled_path)
    if fm is None:
        raise MaterializeError(
            f"assembled skill at {assembled_path} has no SKILL.md frontmatter",
            code=2,
        )
    m = _FRONTMATTER_NAME_RE.search(fm)
    if not m:
        raise MaterializeError(
            f"assembled SKILL.md frontmatter missing `name:` field "
            f"at {assembled_path}",
            code=2,
        )
    return m.group(1)


def parse_delivery_section(spec_path: Path) -> dict:
    """Extract the optional `## Delivery` section from a client spec.

    Returns a dict with keys `present` (bool) and, if present,
    `remote_repo` ("yes" | "no" | None). Stage 11b's driver may use
    this to flip the `gh` default per spec; in 11a it's an exposed
    helper not yet wired into materialize().

    Missing file / missing section → {"present": False, "remote_repo": None}.
    Malformed (Delivery section present but no Remote repo line) →
    {"present": True, "remote_repo": None}.
    """
    if not spec_path.is_file():
        return {"present": False, "remote_repo": None}
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return {"present": False, "remote_repo": None}
    m = _DELIVERY_HEADING_RE.search(text)
    if not m:
        return {"present": False, "remote_repo": None}
    # Look at the body between this heading and the next ## heading or EOF.
    body_start = m.end()
    next_h2 = re.search(r"^##\s", text[body_start:], re.MULTILINE)
    body = (
        text[body_start:body_start + next_h2.start()]
        if next_h2 else text[body_start:]
    )
    rr = _REMOTE_REPO_RE.search(body)
    return {
        "present": True,
        "remote_repo": rr.group(1).lower() if rr else None,
    }


# --------------------------------------------------------------------------
# `gh` CLI wrappers (subprocess.run is the seam tests patch).
# --------------------------------------------------------------------------

def gh_auth_check() -> tuple[bool, str]:
    """Returns (authed, message). False on missing gh, expired auth, or any
    nonzero exit. Message is the gh stderr (or a remediation hint)."""
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False, "gh CLI not installed (try: brew install gh)"
    if proc.returncode == 0:
        return True, proc.stderr.strip() or proc.stdout.strip()
    return False, (
        proc.stderr.strip() or proc.stdout.strip()
        or "gh auth status returned nonzero (try: gh auth login)"
    )


def gh_repo_view(slug: str) -> tuple[bool, str | None]:
    """Returns (exists, url). url is None when exists=False."""
    try:
        proc = subprocess.run(
            ["gh", "repo", "view", f"{GH_OWNER}/{slug}", "--json", "url",
             "-q", ".url"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False, None
    if proc.returncode == 0:
        url = proc.stdout.strip()
        return True, url or None
    return False, None


def gh_repo_create(repo_path: Path, slug: str, *, private: bool = True
                   ) -> tuple[bool, str | None]:
    """Create a remote repo from `repo_path` and push. Returns (ok, url)."""
    visibility = "--private" if private else "--public"
    try:
        proc = subprocess.run(
            ["gh", "repo", "create", f"{GH_OWNER}/{slug}", visibility,
             "--source", str(repo_path), "--push"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False, None
    if proc.returncode != 0:
        return False, proc.stderr.strip() or None
    # Recover the URL via repo view (cheap; gh repo create stdout is
    # human-formatted, not JSON).
    exists, url = gh_repo_view(slug)
    return (True, url) if exists else (True, None)


def gh_add_collaborator(slug: str, user: str = GH_COLLABORATOR
                        ) -> tuple[bool, str | None]:
    """Idempotent — gh's API call is no-op when user is already a
    collaborator (returns 422 or 204 depending on state)."""
    try:
        proc = subprocess.run(
            ["gh", "api", "-X", "PUT",
             f"repos/{GH_OWNER}/{slug}/collaborators/{user}",
             "-f", "permission=push"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False, "gh CLI not installed"
    if proc.returncode == 0:
        return True, None
    # gh returns nonzero on already-collaborator in some versions; check
    # stderr for benign signals.
    err = proc.stderr.strip()
    if "already" in err.lower() or "204" in err:
        return True, None
    return False, err or None


# --------------------------------------------------------------------------
# Filesystem helpers.
# --------------------------------------------------------------------------

_GITIGNORE_BODY = """\
# Editor / OS noise
.DS_Store
*.swp
__pycache__/
*.py[cod]
.venv/
.idea/
.vscode/

# Local-only working trees
/work/
/scratch/
"""


def _ensure_repo(repo_path: Path, company: str,
                 notes: list[str]) -> bool:
    """Make sure `repo_path` is a git repo. Returns True if newly created,
    False if pre-existing. Initializes .gitignore + initial commit on
    create. Existing non-repo directory raises BLOCKER (caller checks)."""
    if (repo_path / ".git").is_dir():
        notes.append(f"repo: reused existing at {repo_path}")
        return False
    repo_path.mkdir(parents=True, exist_ok=True)
    _run_git(repo_path, ["init", "-q", "-b", "main"])
    (repo_path / ".gitignore").write_text(_GITIGNORE_BODY, encoding="utf-8")
    _write_readme(repo_path, company, skills=[])
    _run_git(repo_path, ["add", ".gitignore", "README.md"])
    _run_git(repo_path, ["commit", "-q", "-m",
                         f"Initial commit: {company} Claude skills repo"])
    notes.append(f"repo: initialized fresh at {repo_path}")
    return True


def _write_readme(repo_path: Path, company: str,
                  skills: list[tuple[str, str]]) -> None:
    """Re-generate README.md listing every installed skill. `skills` is a
    list of (slug, description) pairs. Idempotent — overwrites in place."""
    lines = [
        f"# {company} — Claude Skills",
        "",
        f"Per-client skill collection for **{company}**, authored by the "
        f"[Skill Factory](https://github.com/{GH_OWNER}/skill-factory).",
        "",
        "## Installed skills",
        "",
    ]
    if not skills:
        lines.append("_(no skills yet — first skill arrives with the next "
                     "factory run)_")
    else:
        for slug, desc in skills:
            short = desc.strip().splitlines()[0] if desc else ""
            lines.append(f"- **`{slug}`** — {short}" if short
                         else f"- **`{slug}`**")
    lines.append("")
    lines.append("## Activation")
    lines.append("")
    lines.append(
        "Each skill is symlinked into `~/.claude/skills/<slug>/` by the "
        "factory. Re-runs are idempotent — committed code is never "
        "overwritten without a manual `rm -rf`."
    )
    lines.append("")
    (repo_path / "README.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def _list_installed_skills(repo_path: Path) -> list[tuple[str, str]]:
    """Walk the repo root for sub-directories that look like skills (have
    a SKILL.md). Returns sorted (slug, description) pairs."""
    out: list[tuple[str, str]] = []
    for entry in sorted(repo_path.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        desc = _extract_description(skill_md) or ""
        out.append((entry.name, desc))
    return out


def _extract_description(skill_md: Path) -> str | None:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = text[3:end]
    m = re.search(r"^\s*description\s*:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


_GIT_AUTHOR_FLAGS = [
    "-c", "user.name=Skill Factory",
    "-c", "user.email=factory@local",
]


def _run_git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Run `git <args>` in `cwd`. Commit invocations need an author identity
    even when ambient git config is empty (CI, fresh tmpdirs); we inject
    `-c user.name/-c user.email` for commit subcommands so tests work in
    isolated environments without polluting the user's global git config."""
    flags: list[str] = []
    if args and args[0] == "commit":
        flags = _GIT_AUTHOR_FLAGS
    return subprocess.run(
        ["git", *flags, *args], cwd=cwd, capture_output=True, text=True,
        check=True,
    )


def _trees_match(left: Path, right: Path) -> bool:
    """Recursive byte-comparison of two skill directories. Skips `.git/`.
    Returns True iff every file matches (filecmp.cmp shallow=False) AND
    the set of files matches."""
    cmp = filecmp.dircmp(str(left), str(right))
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    for f in cmp.common_files:
        if not filecmp.cmp(left / f, right / f, shallow=False):
            return False
    for d in cmp.common_dirs:
        if d == ".git":
            continue
        if not _trees_match(left / d, right / d):
            return False
    return True


def _copy_skill(assembled_path: Path, dest_skill_path: Path,
                notes: list[str]) -> str:
    """Copy assembled tree to dest. Returns one of:
      "created"   — fresh copy.
      "no-op"     — exists with byte-identical content.
      "conflict"  — exists with different content (BLOCKER signal).
    """
    if dest_skill_path.exists():
        if _trees_match(assembled_path, dest_skill_path):
            notes.append(f"skill: already installed (byte-identical) "
                         f"at {dest_skill_path}")
            return "no-op"
        return "conflict"
    shutil.copytree(assembled_path, dest_skill_path)
    notes.append(f"skill: copied to {dest_skill_path}")
    return "created"


def _ensure_symlink(symlink_path: Path, target: Path,
                    *, force: bool, notes: list[str]) -> str:
    """Make sure symlink_path → target. Returns:
      "created"   — fresh symlink.
      "no-op"     — already pointing at target.
      "replaced"  — was wrong target / real entry, force=True overrode it.
      "conflict"  — wrong target / real entry, force=False BLOCKER signal.
    """
    target = target.resolve() if target.exists() else target
    if symlink_path.is_symlink():
        try:
            current = Path(os.readlink(symlink_path))
        except OSError:
            current = None
        if current is not None and current.resolve() == target:
            notes.append(f"symlink: already correct at {symlink_path}")
            return "no-op"
        if not force:
            return "conflict"
        symlink_path.unlink()
        symlink_path.symlink_to(target)
        notes.append(
            f"symlink: replaced (was {current}) → {target} at {symlink_path}"
        )
        return "replaced"
    if symlink_path.exists():
        # Real file/dir at this name — only --force unlinks it.
        if not force:
            return "conflict"
        if symlink_path.is_dir():
            shutil.rmtree(symlink_path)
        else:
            symlink_path.unlink()
        symlink_path.symlink_to(target)
        notes.append(
            f"symlink: replaced real entry → {target} at {symlink_path}"
        )
        return "replaced"
    symlink_path.parent.mkdir(parents=True, exist_ok=True)
    symlink_path.symlink_to(target)
    notes.append(f"symlink: created → {target} at {symlink_path}")
    return "created"


# --------------------------------------------------------------------------
# Orchestrator.
# --------------------------------------------------------------------------

def materialize(assembled_skill_path: Path, company: str,
                work_dir: Path | None = None, *,
                gh: bool = True, force: bool = False,
                projects_root: Path | None = None,
                skills_registry: Path | None = None,
                ) -> MaterializeResult:
    """Phase 9 entry point. See module docstring for behavior.

    `assembled_skill_path` must point at a gate-passing assembled skill
    (Phase 8 output). `company` is the per-client repo prefix
    (`<company>-claude-skills/`). `work_dir` is reserved for future spec
    lookup (Stage 11b may use it for parse_delivery_section); 11a does
    not consume it.

    `projects_root` / `skills_registry` default to the module-level
    `DEFAULT_PROJECTS_ROOT` / `DEFAULT_SKILLS_REGISTRY` constants. They're
    resolved INSIDE the function body (not as signature defaults) so that
    `unittest.mock.patch.object(ms, "DEFAULT_PROJECTS_ROOT", ...)` can
    redirect tests to a tmpdir without polluting the user's real
    `~/Projects/` or `~/.claude/skills/` (signature defaults bind once at
    import time and would silently bypass the patch).

    Returns a MaterializeResult. The function never raises on BLOCKER
    paths — those return a result with `blocker` set. It DOES raise
    MaterializeError on bad-usage paths (missing assembled dir,
    malformed frontmatter).
    """
    if projects_root is None:
        projects_root = DEFAULT_PROJECTS_ROOT
    if skills_registry is None:
        skills_registry = DEFAULT_SKILLS_REGISTRY
    assembled_skill_path = assembled_skill_path.expanduser().resolve()
    projects_root = projects_root.expanduser()
    skills_registry = skills_registry.expanduser()

    notes: list[str] = []

    if not assembled_skill_path.is_dir():
        raise MaterializeError(
            f"assembled skill path not found: {assembled_skill_path}",
            code=2,
        )

    if is_meta_skill(assembled_skill_path):
        notes.append(
            "meta-skill detected (`meta-skill: true` in frontmatter); "
            "Phase 9 is a no-op for factory-internal artifacts. "
            "Install path is `~/Projects/skill-factory/`, not "
            "`~/Projects/<slug>-claude-skills/`."
        )
        return MaterializeResult(
            installed=False,
            repo_path=None,
            skill_path=None,
            symlink_path=None,
            skipped="meta",
            notes=notes,
        )

    slug = _extract_slug(assembled_skill_path)
    repo_slug = f"{company}-claude-skills"
    repo_path = projects_root / repo_slug
    skill_path = repo_path / slug
    symlink_path = skills_registry / slug

    # Pre-flight: existing non-repo dir at repo_path is a BLOCKER.
    if repo_path.exists() and not (repo_path / ".git").is_dir():
        return MaterializeResult(
            installed=False, repo_path=repo_path,
            skill_path=skill_path, symlink_path=symlink_path,
            blocker=(
                f"path {repo_path} exists but is NOT a git repo. "
                f"Manual resolution: either `git init` it (bless as "
                f"factory-managed) or move it aside."
            ),
            notes=notes,
        )

    installed = False
    repo_created = _ensure_repo(repo_path, company, notes)
    if repo_created:
        installed = True

    copy_status = _copy_skill(assembled_skill_path, skill_path, notes)
    if copy_status == "conflict":
        return MaterializeResult(
            installed=installed, repo_path=repo_path,
            skill_path=skill_path, symlink_path=symlink_path,
            blocker=(
                f"skill directory {skill_path} exists with different "
                f"content. `--force` does NOT bypass — committed code is "
                f"sacred (plan v2 D5). Resolve manually: bump the slug "
                f"(e.g., `{slug}-v2`) or `rm -rf {skill_path}` first."
            ),
            notes=notes,
        )
    if copy_status == "created":
        installed = True

    sym_status = _ensure_symlink(symlink_path, skill_path,
                                 force=force, notes=notes)
    if sym_status == "conflict":
        return MaterializeResult(
            installed=installed, repo_path=repo_path,
            skill_path=skill_path, symlink_path=symlink_path,
            blocker=(
                f"symlink path {symlink_path} exists with wrong target "
                f"or as a real entry. Use `--force` to replace symlinks "
                f"(safe — they're cheap to redo); real entries get "
                f"unlinked too with `--force` and listed in notes."
            ),
            notes=notes,
        )
    if sym_status in ("created", "replaced"):
        installed = True

    # Re-write README to reflect any new skills + commit if anything
    # changed.
    skills_listing = _list_installed_skills(repo_path)
    _write_readme(repo_path, company, skills_listing)
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_path,
        capture_output=True, text=True, check=True,
    )
    if status.stdout.strip():
        _run_git(repo_path, ["add", "-A"])
        _run_git(repo_path, ["commit", "-q", "-m",
                             f"Add/update skill: {slug}"])
        notes.append(f"git: committed skill `{slug}` to {repo_path}")
        installed = True

    gh_url: str | None = None
    if gh:
        gh_result = _do_gh(repo_path, repo_slug, notes)
        if gh_result.get("blocker"):
            return MaterializeResult(
                installed=installed, repo_path=repo_path,
                skill_path=skill_path, symlink_path=symlink_path,
                gh_url=None, blocker=gh_result["blocker"], notes=notes,
            )
        gh_url = gh_result.get("url")

    return MaterializeResult(
        installed=installed, repo_path=repo_path,
        skill_path=skill_path, symlink_path=symlink_path,
        gh_url=gh_url, notes=notes,
    )


def _do_gh(repo_path: Path, repo_slug: str, notes: list[str]) -> dict:
    """Auth + view + create + collaborator. Returns {'blocker': str | None,
    'url': str | None}."""
    authed, msg = gh_auth_check()
    if not authed:
        return {"blocker": f"gh: not authenticated — {msg}", "url": None}

    exists, url = gh_repo_view(repo_slug)
    if exists:
        notes.append(f"gh: remote already exists at {url}")
    else:
        ok, create_msg = gh_repo_create(repo_path, repo_slug, private=True)
        if not ok:
            return {
                "blocker": (
                    f"gh: `gh repo create {GH_OWNER}/{repo_slug}` failed "
                    f"— {create_msg}"
                ),
                "url": None,
            }
        # Re-fetch URL.
        _, url = gh_repo_view(repo_slug)
        notes.append(f"gh: created private remote at {url}")

    coll_ok, coll_err = gh_add_collaborator(repo_slug)
    if not coll_ok:
        notes.append(
            f"gh: WARN — collaborator add for {GH_COLLABORATOR} failed: "
            f"{coll_err}"
        )
    else:
        notes.append(
            f"gh: collaborator {GH_COLLABORATOR} present (push permission)"
        )

    return {"blocker": None, "url": url}


# --------------------------------------------------------------------------
# CLI.
# --------------------------------------------------------------------------

_USAGE = (
    "usage: materialize_skill.py <assembled-path> <company> [<work-dir>] "
    "[--no-gh] [--force]"
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="materialize_skill.py",
        description="Phase 9 of the Skill Factory: install an assembled "
                    "skill into ~/Projects/<company>-claude-skills/ and "
                    "symlink it into ~/.claude/skills/.",
    )
    p.add_argument("assembled_path", type=Path,
                   help="Path to <work>/assembled/<slug>/ from Phase 8.")
    p.add_argument("company",
                   help="Per-client repo prefix (e.g., 'acme').")
    p.add_argument("work_dir", type=Path, nargs="?", default=None,
                   help="(Optional) work tree root for spec lookup. "
                        "Reserved for Stage 11b; not consumed in 11a.")
    p.add_argument("--no-gh", action="store_true",
                   help="Suppress `gh repo create` (default: on per D6).")
    p.add_argument("--force", action="store_true",
                   help="Replace symlinks at ~/.claude/skills/<slug>/ "
                        "even when they point elsewhere or are real "
                        "entries. Never overwrites the skill directory.")
    return p


def _main(argv: list[str]) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv[1:])
    except SystemExit as exc:
        # argparse uses exit code 2 for usage errors — preserve that.
        return int(exc.code) if exc.code is not None else 2

    try:
        result = materialize(
            assembled_skill_path=args.assembled_path,
            company=args.company,
            work_dir=args.work_dir,
            gh=not args.no_gh,
            force=args.force,
        )
    except MaterializeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.blocker:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
