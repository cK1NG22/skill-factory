"""Unit tests for references_lint.py — exercises each of the 3 rules.

Run from skill-references-scaffolder/:
    python3 -m unittest tests.test_references_lint -v
    # or:
    python3 -m pytest tests/ -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
FIXTURES = REPO_SKILL / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import references_lint as rl  # noqa: E402


# ---------- Helpers ----------


def _make_skill(tmp: Path, files: dict[str, str]) -> Path:
    """Materialize a mini skill directory. `files` maps relative paths to
    string contents. Parent dirs are created. Empty-string contents still
    create the file."""
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp


# ---------- Rule A: BP-008 — references/ one level deep ----------


class TestRuleA_BP008(unittest.TestCase):
    def test_flat_references_passes(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)

    def test_nested_subdir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "references/nested/b.md": "# b\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("BP-008" in f and "nested" in f for f in result.fails),
                result.fails,
            )

    def test_deep_subdir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "references/phase-1/scoping/questions.md": "# q\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(any("BP-008" in f for f in result.fails))

    def test_no_references_dir_silent(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nNo refs here.\n",
            })
            # neither trait — the universal rule simply reports info, no fail
            result = rl.lint_paths(skill)
            self.assertTrue(result.passed)
            self.assertTrue(
                any("no references/ directory" in i for i in result.info)
            )

    def test_bp008_runs_even_without_flags(self):
        # Rule A is universal: it fires whenever references/ exists, flags or not.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\n",
                "references/a.md": "# a\n",
                "references/sub/b.md": "# b\n",
            })
            result = rl.lint_paths(skill)  # no flags
            self.assertFalse(result.passed)
            self.assertTrue(any("BP-008" in f for f in result.fails))

    def test_symlinked_subdir_flagged(self):
        # Symlinks to directories should also be caught.
        if os.name == "nt":
            self.skipTest("symlinks unreliable on Windows")
        with tempfile.TemporaryDirectory() as td:
            skill_root = Path(td)
            other = skill_root / "_elsewhere"
            other.mkdir()
            (other / "trap.md").write_text("# trap\n", encoding="utf-8")
            skill = _make_skill(skill_root, {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
            })
            link = skill / "references" / "linked-sub"
            try:
                os.symlink(other, link, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation not permitted")
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed, result.fails)
            self.assertTrue(any("BP-008" in f for f in result.fails))


# ---------- Rule B: BP-007 — citations + inline content ----------


class TestRuleB_BP007_Citations(unittest.TestCase):
    def test_all_cited_passes(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": textwrap.dedent("""
                    # s
                    Read `references/a.md` for A.
                    See `references/b.md` for B.
                """).strip(),
                "references/a.md": "# a\n",
                "references/b.md": "# b\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)

    def test_uncited_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "references/b.md": "# b\n",  # never cited
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("BP-007" in f and "b.md" in f for f in result.fails),
                result.fails,
            )

    def test_non_canonical_cite_warns(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nThe full catalog lives at references/a.md, check it out.\n",
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            # Passes (file IS cited loosely) but emits a warn.
            self.assertTrue(result.passed, result.fails)
            self.assertTrue(
                any("canonical verb" in w for w in result.warns), result.warns
            )

    def test_accepted_verbs_all_pass(self):
        for verb in ["Read", "See", "Consult", "Load", "Use", "Refer to", "per"]:
            with self.subTest(verb=verb):
                with tempfile.TemporaryDirectory() as td:
                    skill = _make_skill(Path(td), {
                        "SKILL.md": f"# s\n{verb} `references/a.md` for A.\n",
                        "references/a.md": "# a\n",
                    })
                    result = rl.lint_paths(skill, has_references=True)
                    self.assertTrue(result.passed, f"{verb}: {result.fails}")
                    self.assertFalse(
                        any("canonical verb" in w for w in result.warns),
                        f"{verb} should be canonical: {result.warns}",
                    )

    def test_has_references_set_but_no_dir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {"SKILL.md": "# s\n"})
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(any("no references/ directory" in f for f in result.fails))

    def test_empty_references_dir_warns(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {"SKILL.md": "# s\n"})
            (Path(td) / "references").mkdir()
            result = rl.lint_paths(skill, has_references=True)
            # No files to cite, no fails; but emits a warn.
            self.assertTrue(result.passed, result.fails)
            self.assertTrue(any("empty" in w for w in result.warns), result.warns)

    def test_has_references_false_skips_citation_check(self):
        # Uncited file should NOT fail when the flag is off.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\n",
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=False)
            self.assertTrue(result.passed, result.fails)

    def test_cite_inside_code_fence_still_counts(self):
        # Code fences are stripped for inline-content detection but NOT for
        # the citation scan — we want to accept shell examples like
        # `python3 ... references/x.md` as a valid mention.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": textwrap.dedent("""
                    # s
                    ```bash
                    cat references/a.md
                    ```
                """).strip(),
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            # The file IS loose-cited (inside fences). No uncited fail.
            uncited = [f for f in result.fails if "not cited" in f]
            self.assertEqual(uncited, [], result.fails)

    def test_unicode_filename_cited(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/strategie-überblick.md` for the map.\n",
                "references/strategie-überblick.md": "# s\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)


class TestRuleB_BP007_InlineContent(unittest.TestCase):
    def test_long_table_fails(self):
        rows = "\n".join(
            [f"| r{i} | a | b |" for i in range(15)]
        )
        text = f"# s\nRead `references/a.md` for A.\n\n{rows}\n"
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": text,
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("inline block" in f for f in result.fails), result.fails
            )

    def test_nine_row_table_passes(self):
        rows = "\n".join([f"| r{i} | a |" for i in range(9)])
        text = f"# s\nRead `references/a.md` for A.\n\n{rows}\n"
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": text,
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)

    def test_long_prose_block_fails(self):
        prose = "\n".join(
            [f"Line {i} carries content that is not a heading." for i in range(25)]
        )
        text = f"# s\nRead `references/a.md` for A.\n\n{prose}\n"
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": text,
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(any("inline block" in f for f in result.fails))

    def test_prose_broken_by_headings_passes(self):
        # Alternating headings prevent the 20-line dense streak from forming.
        blocks = []
        for i in range(5):
            blocks.append(f"### Subsection {i}")
            blocks.append(f"Short body for subsection {i}.")
            blocks.append("")
        text = "# s\nRead `references/a.md` for A.\n\n" + "\n".join(blocks)
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": text,
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)

    def test_long_table_inside_code_fence_passes(self):
        rows = "\n".join([f"| r{i} | a |" for i in range(20)])
        text = (
            "# s\nRead `references/a.md` for A.\n\n"
            f"```markdown\n{rows}\n```\n"
        )
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": text,
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            # Code-fenced table is example content — must not trip inline-block rule.
            self.assertTrue(result.passed, result.fails)


# ---------- Rule C: BP-009 — parallel folders ----------


class TestRuleC_BP009(unittest.TestCase):
    def test_parallel_folders_pass(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# phase1\n",
                "assets/tmpl.txt": "tmpl",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=True)
            self.assertTrue(result.passed, result.fails)

    def test_phases_slash_references_nested_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# phase1\n",
                "phases/01/references/deep.md": "# deep\n",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("BP-009" in f and "nested" in f for f in result.fails),
                result.fails,
            )

    def test_references_slash_phases_nested_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "references/weird/phases/x.md": "# weird\n",
                "phases/01/input.md": "# phase1\n",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=True)
            self.assertFalse(result.passed)
            # Nested references-subdir ALSO trips BP-008; we only care that the
            # BP-009 fail is surfaced.
            self.assertTrue(any("BP-009" in f for f in result.fails), result.fails)

    def test_missing_phases_dir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("BP-009" in f and "phases/" in f for f in result.fails),
                result.fails,
            )

    def test_missing_assets_warns_not_fails(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# phase1\n",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=True)
            self.assertTrue(result.passed, result.fails)
            self.assertTrue(
                any("assets/" in w for w in result.warns), result.warns
            )

    def test_has_phases_false_skips_structure_check(self):
        # A phases/<X>/references layout must NOT fail when has_phases is off
        # (we only enforce structural parity when the trait fires).
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/references/deep.md": "# deep\n",
            })
            result = rl.lint_paths(skill, has_references=True, has_phases=False)
            # BP-009 fail absent; only BP-007 citation + BP-008 on references/
            # (references/ itself is flat — deep is under phases/).
            bp009 = [f for f in result.fails if "BP-009" in f]
            self.assertEqual(bp009, [], result.fails)


# ---------- End-to-end on real fixtures ----------


class TestFixturesEndToEnd(unittest.TestCase):
    def test_passing_fixture_passes(self):
        skill = FIXTURES / "passing-skill"
        result = rl.lint_paths(skill, has_references=True)
        self.assertTrue(result.passed, result.fails)

    def test_passing_with_phases_fixture_passes(self):
        skill = FIXTURES / "passing-with-phases-skill"
        result = rl.lint_paths(skill, has_references=True, has_phases=True)
        self.assertTrue(result.passed, result.fails)

    def test_gaps_fixture_fails_with_all_four_categories(self):
        skill = FIXTURES / "gaps-skill"
        result = rl.lint_paths(skill, has_references=True, has_phases=True)
        self.assertFalse(result.passed)
        joined = " | ".join(result.fails)
        # BP-008 subdir
        self.assertIn("BP-008", joined)
        # BP-007 uncited
        self.assertIn("anti-patterns.md", joined)
        # BP-007 inline content
        self.assertIn("inline block", joined)
        # BP-009 nested
        self.assertIn("BP-009", joined)


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def test_cli_passing(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py"),
             str(FIXTURES / "passing-skill"), "--has-references"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_passing_with_phases(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py"),
             str(FIXTURES / "passing-with-phases-skill"),
             "--has-references", "--has-phases"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_gaps_fails(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py"),
             str(FIXTURES / "gaps-skill"),
             "--has-references", "--has-phases"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertFalse(data["passed"])
        self.assertGreater(len(data["fails"]), 0)

    def test_cli_bad_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_missing_target(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py"),
             "/nonexistent/path/xyz"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_skill_md_arg(self):
        # Passing a SKILL.md path should work — parent dir is treated as skill dir.
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "references_lint.py"),
             str(FIXTURES / "passing-skill" / "SKILL.md"),
             "--has-references"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


# ---------- Edge cases ----------


class TestEdgeCases(unittest.TestCase):
    def test_missing_skill_md_with_has_references_still_reports(self):
        # If SKILL.md is absent, uncited-file fail should surface on every file.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "references/a.md": "# a\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("not cited" in f for f in result.fails), result.fails
            )

    def test_skill_dir_itself_missing(self):
        result = rl.lint_paths(Path("/nonexistent/deadbeef"))
        self.assertFalse(result.passed)
        self.assertTrue(any("not found" in f for f in result.fails))

    def test_citation_with_different_indentation(self):
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": textwrap.dedent("""
                    # s

                    - Step 1: Read `references/a.md` for A.
                    - Step 2: Consult `references/b.md` for B.
                """).strip(),
                "references/a.md": "# a\n",
                "references/b.md": "# b\n",
            })
            result = rl.lint_paths(skill, has_references=True)
            self.assertTrue(result.passed, result.fails)


if __name__ == "__main__":
    unittest.main()
