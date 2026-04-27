"""Unit tests for materialize_skill.py (Stage 11a).

Run from skill-factory/:
    python3 -m unittest tests.test_materialize_skill -v

Coverage map (per plan v2 §"Stage 11a — Unit tests in test_materialize_skill.py"):

  TestRepoCreation         x3  — fresh dir → .gitignore + README + commit
  TestRepoIdempotency      x3  — existing repo reused, README updated, commit
  TestSkillCopy            x3  — tree copied, manifest preserved, modes preserved
  TestSymlinkCreation      x4  — correct, no-op, BLOCKER on wrong target,
                                  BLOCKER on real entry
  TestMetaSkillSkip        x2  — short-circuit on marker, no skip without
  TestDeliverySection      x4  — yes, no, missing section, malformed
  TestGhIntegration        x6  — auth pass/fail, view exists/missing,
                                  create success/fail (subprocess mocked)
  TestForceFlag            x2  — overrides BLOCKER on wrong-target symlink +
                                  real-entry-at-symlink-path
  TestCli                  x3  — exit 0 (success), 1 (BLOCKER), 2 (bad usage)

  Total: 30 tests.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
FIXTURES = REPO_SKILL / "fixtures" / "stage-11a"

sys.path.insert(0, str(SCRIPTS))
import materialize_skill as ms  # noqa: E402


# --------------------------------------------------------------------------
# Shared helpers.
# --------------------------------------------------------------------------

class _MaterializeBase(unittest.TestCase):
    """Sets up tmp `projects_root` + `skills_registry` per test. Production
    callers (the driver) use the real `~/Projects/` and `~/.claude/skills/`
    via the script's defaults; tests inject tmp paths via the
    materialize() kwargs."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmp.name)
        self.projects_root = self.tmp_root / "Projects"
        self.skills_registry = self.tmp_root / "claude-skills"
        self.projects_root.mkdir()
        self.skills_registry.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _materialize(self, fixture_name: str, company: str, **kw):
        """Convenience wrapper. fixture_name is a subdir of fixtures/stage-11a/."""
        return ms.materialize(
            assembled_skill_path=FIXTURES / fixture_name,
            company=company,
            projects_root=self.projects_root,
            skills_registry=self.skills_registry,
            gh=kw.pop("gh", False),
            force=kw.pop("force", False),
            **kw,
        )


# --------------------------------------------------------------------------
# TestRepoCreation — 3 tests.
# --------------------------------------------------------------------------

class TestRepoCreation(_MaterializeBase):
    """Fresh repo creation: .gitignore + README + initial commit."""

    def test_creates_gitignore_with_expected_lines(self):
        self._materialize("assembled-acme-board-memo", "acme")
        gi = (self.projects_root / "acme-claude-skills" / ".gitignore").read_text()
        self.assertIn(".DS_Store", gi)
        self.assertIn("__pycache__/", gi)
        self.assertIn("/work/", gi)

    def test_creates_readme_listing_the_first_skill(self):
        self._materialize("assembled-acme-board-memo", "acme")
        readme = (self.projects_root / "acme-claude-skills" / "README.md").read_text()
        self.assertIn("# acme — Claude Skills", readme)
        self.assertIn("`acme-board-memo`", readme)

    def test_creates_initial_commit_with_author_factory(self):
        self._materialize("assembled-acme-board-memo", "acme")
        repo = self.projects_root / "acme-claude-skills"
        log = subprocess.run(
            ["git", "log", "--format=%an|%ae|%s"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        # Two commits: initial + skill add. Initial is the older (last line).
        lines = log.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        initial = lines[-1]
        self.assertIn("Skill Factory", initial)
        self.assertIn("factory@local", initial)
        self.assertIn("Initial commit", initial)


# --------------------------------------------------------------------------
# TestRepoIdempotency — 3 tests.
# --------------------------------------------------------------------------

class TestRepoIdempotency(_MaterializeBase):
    """Re-running for the same company appends, never re-inits."""

    def test_second_run_reuses_existing_repo_no_reinit(self):
        first = self._materialize("assembled-acme-board-memo", "acme")
        # Mark the .git dir to detect re-init.
        marker = self.projects_root / "acme-claude-skills" / ".git" / "FACTORY-MARKER"
        marker.write_text("preserved")
        # Second run with same fixture — should be byte-identical → no-op.
        second = self._materialize("assembled-acme-board-memo", "acme")
        self.assertTrue(marker.exists(),
                        "second run must NOT re-init the .git dir")
        self.assertIsNone(second.blocker)
        self.assertIn("reused existing", " ".join(first.notes + second.notes))

    def test_byte_identical_second_run_is_no_op_no_new_commit(self):
        self._materialize("assembled-acme-board-memo", "acme")
        repo = self.projects_root / "acme-claude-skills"
        before = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout.strip()
        result = self._materialize("assembled-acme-board-memo", "acme")
        after = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(before, after,
                         "byte-identical re-run must not create a new commit")
        self.assertIsNone(result.blocker)
        self.assertFalse(result.installed,
                         "no-op re-run reports installed=False")

    def test_second_skill_for_same_company_updates_readme(self):
        self._materialize("assembled-acme-board-memo", "acme")
        # Use the conflict fixture as a second, different skill (different name).
        self._materialize("assembled-existing-conflict", "acme")
        readme = (self.projects_root / "acme-claude-skills" / "README.md").read_text()
        self.assertIn("`acme-board-memo`", readme)
        self.assertIn("`acme-conflict-skill`", readme)
        # Verify a third commit landed (initial + 2 skill commits).
        repo = self.projects_root / "acme-claude-skills"
        n = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(n, "3")


# --------------------------------------------------------------------------
# TestSkillCopy — 3 tests.
# --------------------------------------------------------------------------

class TestSkillCopy(_MaterializeBase):
    """Skill directory copied verbatim with manifest + modes preserved."""

    def test_full_subtree_copied(self):
        self._materialize("assembled-acme-board-memo", "acme")
        dst = self.projects_root / "acme-claude-skills" / "acme-board-memo"
        self.assertTrue((dst / "SKILL.md").is_file())
        self.assertTrue((dst / "references" / "template.md").is_file())
        self.assertTrue((dst / "scripts" / "render_memo.py").is_file())

    def test_assembly_manifest_preserved(self):
        self._materialize("assembled-acme-board-memo", "acme")
        dst = self.projects_root / "acme-claude-skills" / "acme-board-memo"
        manifest = json.loads((dst / "ASSEMBLY-MANIFEST.json").read_text())
        self.assertEqual(manifest["slug"], "acme-board-memo")
        self.assertIn("has_phases", manifest["firing_traits"])

    def test_file_permissions_preserved(self):
        # Make the source script executable; verify the copy is too.
        src_script = (FIXTURES / "assembled-acme-board-memo"
                      / "scripts" / "render_memo.py")
        original_mode = src_script.stat().st_mode
        try:
            src_script.chmod(0o755)
            self._materialize("assembled-acme-board-memo", "acme")
            dst_script = (self.projects_root / "acme-claude-skills"
                          / "acme-board-memo" / "scripts" / "render_memo.py")
            self.assertTrue(os.access(dst_script, os.X_OK),
                            "copytree should preserve the executable bit")
        finally:
            src_script.chmod(original_mode)


# --------------------------------------------------------------------------
# TestSymlinkCreation — 4 tests.
# --------------------------------------------------------------------------

class TestSymlinkCreation(_MaterializeBase):
    """Symlink shape per plan v2 D4."""

    def test_symlink_points_at_repo_skill_path(self):
        self._materialize("assembled-acme-board-memo", "acme")
        sym = self.skills_registry / "acme-board-memo"
        self.assertTrue(sym.is_symlink())
        target = Path(os.readlink(sym))
        expected = self.projects_root / "acme-claude-skills" / "acme-board-memo"
        self.assertEqual(target.resolve(), expected.resolve())

    def test_correct_existing_symlink_is_no_op(self):
        self._materialize("assembled-acme-board-memo", "acme")
        before_mtime = (self.skills_registry / "acme-board-memo").lstat().st_mtime
        result = self._materialize("assembled-acme-board-memo", "acme")
        after_mtime = (self.skills_registry / "acme-board-memo").lstat().st_mtime
        self.assertEqual(before_mtime, after_mtime,
                         "correct symlink must not be touched")
        self.assertIsNone(result.blocker)

    def test_wrong_target_symlink_blocks_without_force(self):
        # Pre-seed a misdirected symlink.
        sym = self.skills_registry / "acme-board-memo"
        bogus = self.tmp_root / "bogus-target"
        bogus.mkdir()
        sym.symlink_to(bogus)
        result = self._materialize("assembled-acme-board-memo", "acme")
        self.assertIsNotNone(result.blocker)
        self.assertIn("symlink", result.blocker.lower())
        # And the bad symlink is preserved (we did NOT silently overwrite).
        self.assertTrue(sym.is_symlink())
        self.assertEqual(Path(os.readlink(sym)), bogus)

    def test_real_entry_at_symlink_path_blocks_without_force(self):
        sym = self.skills_registry / "acme-board-memo"
        sym.mkdir()
        (sym / "hand-authored-skill.md").write_text("hand-rolled")
        result = self._materialize("assembled-acme-board-memo", "acme")
        self.assertIsNotNone(result.blocker)
        # Hand-rolled file preserved (no silent destruction).
        self.assertTrue((sym / "hand-authored-skill.md").is_file())


# --------------------------------------------------------------------------
# TestMetaSkillSkip — 2 tests.
# --------------------------------------------------------------------------

class TestMetaSkillSkip(_MaterializeBase):
    """Plan v2 D7: meta-skills short-circuit Phase 9."""

    def test_meta_marker_short_circuits_no_filesystem_changes(self):
        result = self._materialize("assembled-skill-factory-meta",
                                   "skill-factory")
        self.assertEqual(result.skipped, "meta")
        self.assertFalse(result.installed)
        self.assertIsNone(result.blocker)
        # Filesystem unchanged.
        self.assertEqual(list(self.projects_root.iterdir()), [])
        self.assertEqual(list(self.skills_registry.iterdir()), [])

    def test_non_meta_does_not_skip(self):
        self.assertFalse(ms.is_meta_skill(
            FIXTURES / "assembled-acme-board-memo"
        ))
        result = self._materialize("assembled-acme-board-memo", "acme")
        self.assertIsNone(result.skipped)
        self.assertTrue(result.installed)


# --------------------------------------------------------------------------
# TestDeliverySection — 4 tests.
# --------------------------------------------------------------------------

class TestDeliverySection(unittest.TestCase):
    """parse_delivery_section() — the helper Stage 11b will wire up."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _spec(self, body: str) -> Path:
        p = self.tmp / "spec.md"
        p.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
        return p

    def test_remote_repo_yes(self):
        spec = self._spec("""
            # Spec

            ## Delivery

            Remote repo: yes
        """)
        self.assertEqual(
            ms.parse_delivery_section(spec),
            {"present": True, "remote_repo": "yes"},
        )

    def test_remote_repo_no(self):
        spec = self._spec("""
            # Spec

            ## Delivery

            Remote repo: no
        """)
        self.assertEqual(
            ms.parse_delivery_section(spec),
            {"present": True, "remote_repo": "no"},
        )

    def test_missing_section(self):
        spec = self._spec("""
            # Spec

            ## Some Other Section

            blah blah
        """)
        self.assertEqual(
            ms.parse_delivery_section(spec),
            {"present": False, "remote_repo": None},
        )

    def test_malformed_section_present_but_no_remote_repo_line(self):
        spec = self._spec("""
            # Spec

            ## Delivery

            Some unrelated note about delivery.
        """)
        self.assertEqual(
            ms.parse_delivery_section(spec),
            {"present": True, "remote_repo": None},
        )


# --------------------------------------------------------------------------
# TestGhIntegration — 6 tests (subprocess.run is mocked).
# --------------------------------------------------------------------------

def _fake_proc(returncode: int = 0, stdout: str = "", stderr: str = ""
               ) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode,
                                       stdout=stdout, stderr=stderr)


class TestGhIntegration(unittest.TestCase):
    """All gh paths exercised via mocked subprocess.run."""

    def test_gh_auth_check_pass(self):
        with mock.patch("materialize_skill.subprocess.run",
                        return_value=_fake_proc(0, stderr="Logged in to github.com")):
            ok, msg = ms.gh_auth_check()
        self.assertTrue(ok)
        self.assertIn("Logged in", msg)

    def test_gh_auth_check_fail(self):
        with mock.patch("materialize_skill.subprocess.run",
                        return_value=_fake_proc(1, stderr="not logged in")):
            ok, msg = ms.gh_auth_check()
        self.assertFalse(ok)
        self.assertIn("not logged in", msg)

    def test_gh_repo_view_exists(self):
        with mock.patch("materialize_skill.subprocess.run",
                        return_value=_fake_proc(0, stdout="https://github.com/ck22coding/acme-claude-skills")):
            exists, url = ms.gh_repo_view("acme-claude-skills")
        self.assertTrue(exists)
        self.assertEqual(url, "https://github.com/ck22coding/acme-claude-skills")

    def test_gh_repo_view_missing(self):
        with mock.patch("materialize_skill.subprocess.run",
                        return_value=_fake_proc(1, stderr="not found")):
            exists, url = ms.gh_repo_view("acme-claude-skills")
        self.assertFalse(exists)
        self.assertIsNone(url)

    def test_gh_repo_create_success_recovers_url_via_view(self):
        # First call (create) returns ok; second (view, called inside create)
        # returns the URL.
        calls = [
            _fake_proc(0, stdout=""),
            _fake_proc(0, stdout="https://github.com/ck22coding/acme-claude-skills"),
        ]
        with mock.patch("materialize_skill.subprocess.run",
                        side_effect=calls):
            ok, url = ms.gh_repo_create(Path("/tmp/fake"),
                                        "acme-claude-skills",
                                        private=True)
        self.assertTrue(ok)
        self.assertEqual(url, "https://github.com/ck22coding/acme-claude-skills")

    def test_gh_repo_create_failure_returns_stderr(self):
        with mock.patch("materialize_skill.subprocess.run",
                        return_value=_fake_proc(1, stderr="rate limited")):
            ok, msg = ms.gh_repo_create(Path("/tmp/fake"),
                                        "acme-claude-skills",
                                        private=True)
        self.assertFalse(ok)
        self.assertIn("rate", (msg or "").lower())


# --------------------------------------------------------------------------
# TestForceFlag — 2 tests.
# --------------------------------------------------------------------------

class TestForceFlag(_MaterializeBase):
    """--force replaces SYMLINKS only (plan v2 D5 + Q5)."""

    def test_force_replaces_wrong_target_symlink(self):
        sym = self.skills_registry / "acme-board-memo"
        bogus = self.tmp_root / "old-target"
        bogus.mkdir()
        sym.symlink_to(bogus)
        result = self._materialize("assembled-acme-board-memo", "acme",
                                   force=True)
        self.assertIsNone(result.blocker)
        self.assertTrue(sym.is_symlink())
        new_target = Path(os.readlink(sym)).resolve()
        expected = (self.projects_root / "acme-claude-skills"
                    / "acme-board-memo").resolve()
        self.assertEqual(new_target, expected)
        self.assertTrue(any("replaced" in n for n in result.notes))

    def test_force_replaces_real_entry_at_symlink_path(self):
        sym = self.skills_registry / "acme-board-memo"
        sym.mkdir()
        (sym / "hand-authored.md").write_text("hand-rolled")
        result = self._materialize("assembled-acme-board-memo", "acme",
                                   force=True)
        self.assertIsNone(result.blocker)
        self.assertTrue(sym.is_symlink())
        # Hand-authored content is gone — but a note was logged about it.
        self.assertFalse((sym.parent / "acme-board-memo"
                          / "hand-authored.md").exists())
        self.assertTrue(any("replaced real entry" in n for n in result.notes))


# --------------------------------------------------------------------------
# TestCli — 3 tests.
# --------------------------------------------------------------------------

class TestCli(unittest.TestCase):
    """Exit codes 0 (success), 1 (BLOCKER), 2 (bad usage)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # The CLI uses real DEFAULT_PROJECTS_ROOT/SKILLS_REGISTRY paths
        # (we can't override via flags). We patch them at the module level
        # so the CLI test doesn't touch ~/Projects/ or ~/.claude/skills/.
        self._patches = [
            mock.patch.object(ms, "DEFAULT_PROJECTS_ROOT", self.tmp / "Projects"),
            mock.patch.object(ms, "DEFAULT_SKILLS_REGISTRY",
                              self.tmp / "skills"),
        ]
        for p in self._patches:
            p.start()
        (self.tmp / "Projects").mkdir()
        (self.tmp / "skills").mkdir()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def test_exit_0_on_success(self):
        rc = ms._main([
            "materialize_skill.py",
            str(FIXTURES / "assembled-acme-board-memo"),
            "acme", "--no-gh",
        ])
        self.assertEqual(rc, 0)

    def test_exit_1_on_blocker(self):
        # Pre-seed a wrong-target symlink so materialize() returns blocker.
        sym = self.tmp / "skills" / "acme-board-memo"
        bogus = self.tmp / "bogus"
        bogus.mkdir()
        sym.symlink_to(bogus)
        rc = ms._main([
            "materialize_skill.py",
            str(FIXTURES / "assembled-acme-board-memo"),
            "acme", "--no-gh",
        ])
        self.assertEqual(rc, 1)

    def test_exit_2_on_bad_usage(self):
        # Missing required `company` arg → argparse exits 2.
        rc = ms._main(["materialize_skill.py"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
