"""Unit tests for fixture_paths.py — the {{REPO_ROOT}} resolver.

Run from skill-factory/:
    python3 -m unittest tests.test_fixture_paths -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
REPO_ROOT = REPO_SKILL.parent

sys.path.insert(0, str(SCRIPTS))
import fixture_paths as fp  # noqa: E402


class TestRepoRoot(unittest.TestCase):
    def test_default_anchor_resolves_to_repo_root(self):
        """No anchor → uses fixture_paths.py's own __file__, which is two
        parents up from the repo root (scripts/ → skill-factory/ → root)."""
        self.assertEqual(fp.repo_root(), REPO_ROOT)

    def test_repo_root_contains_patterns_dir(self):
        """Sanity check the anchor: the resolved root must hold the
        `patterns/` tree the placeholder is meant to point at."""
        self.assertTrue((fp.repo_root() / "patterns").is_dir())

    def test_explicit_anchor_overrides_default(self):
        """Passing an anchor lets callers (and tests) simulate a different
        install location without monkeypatching __file__."""
        fake = Path("/tmp/fake/skill-factory/scripts/fixture_paths.py")
        self.assertEqual(fp.repo_root(anchor=fake), Path("/tmp/fake"))


class TestExpandRepoRoot(unittest.TestCase):
    def test_substitutes_placeholder(self):
        text = "- {{REPO_ROOT}}/patterns/bp-001.md\n"
        out = fp.expand_repo_root(text)
        self.assertEqual(out, f"- {REPO_ROOT}/patterns/bp-001.md\n")

    def test_idempotent_without_placeholder(self):
        text = "no placeholder here, just prose.\n"
        self.assertEqual(fp.expand_repo_root(text), text)

    def test_replaces_every_occurrence(self):
        text = "{{REPO_ROOT}}/a\n{{REPO_ROOT}}/b\n"
        out = fp.expand_repo_root(text)
        self.assertNotIn(fp.PLACEHOLDER, out)
        self.assertEqual(out.count(str(REPO_ROOT)), 2)

    def test_explicit_root_overrides(self):
        text = "{{REPO_ROOT}}/x"
        out = fp.expand_repo_root(text, root=Path("/srv/clone"))
        self.assertEqual(out, "/srv/clone/x")


class TestCLI(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "fixture_paths.py"), *args],
            capture_output=True, text=True,
        )

    def test_cli_expands_fixture(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("path: {{REPO_ROOT}}/patterns/bp-001.md\n")
            p = f.name
        try:
            result = self._run(p)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"path: {REPO_ROOT}/patterns/bp-001.md", result.stdout)
            self.assertNotIn(fp.PLACEHOLDER, result.stdout)
        finally:
            Path(p).unlink()

    def test_cli_missing_file_returns_1(self):
        result = self._run("/tmp/does-not-exist-xyz-12345.md")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a file", result.stderr)

    def test_cli_no_args_returns_2(self):
        result = self._run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
