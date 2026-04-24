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


class TestStage904TwoLevelHierarchy(unittest.TestCase):
    """Tests for the --two-level flag introduced in Stage 9.0.4.

    Two-level mode is the Skill Factory's director hierarchy: top-level
    SKILL.md directs to phases/<N>/director.md, and each phase director
    directs to phase-scoped phases/<N>/references/<file>.md. Nesting of
    `phases/<N>/references/` is the canonical pattern, not a BP-009 fail.
    `references/<X>/phases/` remains nonsensical and still fails.
    """

    def test_two_level_false_still_fails_on_nested(self):
        # Backward compat: without --two-level, the old Rule C still hard-fails
        # on phases/<N>/references/ nesting.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# p\n",
                "phases/01/references/scoped.md": "# scoped\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True, two_level=False,
            )
            self.assertFalse(result.passed)
            self.assertTrue(
                any("BP-009" in f and "nested" in f for f in result.fails),
                result.fails,
            )

    def test_two_level_true_accepts_scoped_references(self):
        # With --two-level AND --has-phases, phases/<N>/references/ is legit.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# p\n",
                "phases/01/references/scoped.md": "# scoped\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True, two_level=True,
            )
            # No BP-009 nested fail when two-level is on.
            self.assertFalse(
                any("BP-009" in f and "nested" in f for f in result.fails),
                f"Unexpected BP-009 nested fail under two-level mode: {result.fails}",
            )

    def test_two_level_emits_info_counting_scoped_dirs(self):
        # When two-level legitimizes the nesting, surface it as info so the
        # operator can see how many phase-dirs carry scoped refs.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# p\n",
                "phases/01/references/one.md": "# one\n",
                "phases/02/input.md": "# p\n",
                "phases/02/references/two.md": "# two\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True, two_level=True,
            )
            info_lines = " ".join(result.info)
            self.assertIn("two-level hierarchy detected", info_lines)
            # Both phase-scoped refs dirs reported.
            self.assertIn("phases/01/references", info_lines)
            self.assertIn("phases/02/references", info_lines)

    def test_two_level_still_fails_on_reversed_nesting(self):
        # references/<X>/phases/ is nonsensical in either mode. --two-level
        # only legitimizes phases/<N>/references/, not the reverse.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "references/oops/phases/x.md": "# reversed nest\n",
                "phases/01/input.md": "# p\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True, two_level=True,
            )
            # BP-009 must still surface on the reversed nest.
            self.assertTrue(
                any("BP-009" in f for f in result.fails), result.fails,
            )

    def test_cli_two_level_flag(self):
        # CLI surfaces the flag and accepts it.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/a.md` for A.\n",
                "references/a.md": "# a\n",
                "phases/01/input.md": "# p\n",
                "phases/01/references/scoped.md": "# scoped\n",
            })
            script = SCRIPTS / "references_lint.py"
            proc = subprocess.run(
                ["python3", str(script), str(skill),
                 "--has-references", "--has-phases", "--two-level"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = json.loads(proc.stdout)
            self.assertTrue(out["passed"])
            self.assertTrue(
                any("two-level hierarchy detected" in i for i in out["info"]),
                out["info"],
            )


class TestStage906StrictCitationWalk(unittest.TestCase):
    """Tests for --strict-two-level introduced in Stage 9.0.6.

    Strict mode closes the warn-only window that 9.0.4 opened. It enforces
    citation topology on top of the structural rules:

      1. Each phase-scoped ref under `phases/<N>/references/<file>.md` MUST
         be cited from `phases/<N>/director.md` (its own phase's director).
      2. Each cross-phase ref under top-level `references/<file>.md` MUST
         be cited from SKILL.md OR from ≥2 phase directors (otherwise it's
         orphan — either it belongs under a single phase or it's dead code).

    `--strict-two-level` implies `--two-level` as a convenience.
    """

    def _canonical_two_level_skill(self, td: Path) -> Path:
        """Build a minimal two-level tree that satisfies strict mode:
        - one cross-phase ref cited from SKILL.md
        - two phase-scoped refs each cited by their own director
        """
        return _make_skill(td, {
            "SKILL.md": textwrap.dedent("""
                # driver
                Read `references/shared.md` for the shared mechanic.
                See `phases/01/director.md` for phase 1.
                See `phases/02/director.md` for phase 2.
            """).strip(),
            "references/shared.md": "# shared\n",
            "phases/01/director.md": "# phase 1\nRead `references/one.md` for the phase-1 detail.\n",
            "phases/01/references/one.md": "# one\n",
            "phases/02/director.md": "# phase 2\nRead `references/two.md` for the phase-2 detail.\n",
            "phases/02/references/two.md": "# two\n",
        })

    def test_strict_happy_path_passes(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self._canonical_two_level_skill(Path(td))
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertTrue(result.passed, result.fails)
            # info line should report how many directors were walked.
            self.assertTrue(
                any("strict citation-walk" in i and "2 phase director" in i
                    for i in result.info),
                result.info,
            )

    def test_strict_phase_scoped_ref_not_cited_by_own_director_fails(self):
        # phase-1 has a scoped ref, but phase-1/director.md doesn't cite it.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# s\nRead `references/shared.md` for shared.\nSee `phases/01/director.md`.\n",
                "references/shared.md": "# shared\n",
                "phases/01/director.md": "# phase 1\nNothing cited here.\n",
                "phases/01/references/orphan.md": "# orphan\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertFalse(result.passed)
            self.assertTrue(
                any("phase-scoped ref" in f and "orphan.md" in f
                    and "director.md" in f for f in result.fails),
                result.fails,
            )

    def test_strict_phase_scoped_ref_cited_only_from_skill_md_fails(self):
        # SKILL.md citing a phase-scoped ref does NOT rescue it. The own
        # phase director is the only valid citer under strict mode.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": textwrap.dedent("""
                    # driver
                    Read `phases/01/references/leaked.md` for something.
                    See `phases/01/director.md`.
                """).strip(),
                "phases/01/director.md": "# phase 1\nNo citations here.\n",
                "phases/01/references/leaked.md": "# leaked\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertFalse(result.passed)
            self.assertTrue(
                any("phase-scoped ref" in f and "leaked.md" in f
                    for f in result.fails),
                result.fails,
            )

    def test_strict_cross_phase_ref_orphan_fails(self):
        # references/unused.md exists but is cited from neither SKILL.md
        # nor from any phase director.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# driver\nSee `phases/01/director.md`.\n",
                "references/unused.md": "# unused\n",
                "phases/01/director.md": "# phase 1\nNo ref mentions.\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertFalse(result.passed)
            # BP-007 ALSO fails (uncited from SKILL.md); we only assert that
            # the strict-mode orphan fail is also present with its own wording.
            self.assertTrue(
                any("cross-phase ref" in f and "orphan under strict two-level"
                    in f for f in result.fails),
                result.fails,
            )

    def test_strict_cross_phase_ref_cited_from_two_directors_passes(self):
        # Shared ref cited from 2 phase directors (not SKILL.md) satisfies
        # the ≥2-directors disjunct.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                # SKILL.md cites shared.md with a canonical verb so Rule B passes.
                "SKILL.md": textwrap.dedent("""
                    # driver
                    Read `references/shared.md` for the shared mechanic.
                    See `phases/01/director.md`.
                    See `phases/02/director.md`.
                """).strip(),
                "references/shared.md": "# shared\n",
                "phases/01/director.md": "# phase 1\nSee `references/shared.md` for the shared detail.\n",
                "phases/02/director.md": "# phase 2\nSee `references/shared.md` for the shared detail.\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertTrue(result.passed, result.fails)

    def test_strict_cross_phase_ref_cited_from_single_director_fails(self):
        # Exactly 1 phase director citing (not SKILL.md) → below the ≥2
        # threshold → orphan fail. This guards the boundary on the disjunct.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                # SKILL.md still needs to satisfy Rule B so the orphan fail
                # we're asserting is the strict-mode one, not the BP-007 one.
                # Cite `solo.md` loosely (non-canonical) so BP-007 doesn't fire
                # "uncited" but the canonical-citation check in strict mode
                # still sees it as "not cited from SKILL.md".
                #
                # Actually _citations_in uses the loose regex, so ANY mention
                # in SKILL.md counts as "cited from SKILL.md" under strict
                # mode. To make this test isolate the "single-director"
                # boundary, keep SKILL.md silent on solo.md and accept the
                # BP-007 uncited fail as a co-occurrence.
                "SKILL.md": "# driver\nSee `phases/01/director.md`.\n",
                "references/solo.md": "# solo\n",
                "phases/01/director.md": "# phase 1\nSee `references/solo.md` for detail.\n",
            })
            result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertFalse(result.passed)
            self.assertTrue(
                any("cross-phase ref" in f and "solo.md" in f
                    and "orphan under strict two-level" in f
                    for f in result.fails),
                result.fails,
            )

    def test_strict_default_off_warn_mode_accepts_same_topology(self):
        # The same topology that fails under strict mode must pass under
        # warn-only mode (strict_two_level=False). Regression guard on the
        # behavior-change semantics of the flag.
        with tempfile.TemporaryDirectory() as td:
            skill = _make_skill(Path(td), {
                "SKILL.md": "# driver\nRead `references/shared.md` for shared.\nSee `phases/01/director.md`.\n",
                "references/shared.md": "# shared\n",
                "phases/01/director.md": "# phase 1\nNo citations here.\n",
                "phases/01/references/orphan.md": "# orphan\n",
            })
            # warn-only: no strict_two_level → no strict fails
            warn_result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=False,
            )
            self.assertTrue(
                all("strict" not in f for f in warn_result.fails),
                warn_result.fails,
            )
            # strict-on: same topology now fails.
            strict_result = rl.lint_paths(
                skill, has_references=True, has_phases=True,
                two_level=True, strict_two_level=True,
            )
            self.assertFalse(strict_result.passed)

    def test_cli_strict_two_level_flag_implies_two_level(self):
        # `--strict-two-level` alone (without `--two-level`) should still
        # work because strict implies two-level.
        with tempfile.TemporaryDirectory() as td:
            skill = self._canonical_two_level_skill(Path(td))
            script = SCRIPTS / "references_lint.py"
            proc = subprocess.run(
                [sys.executable, str(script), str(skill),
                 "--has-references", "--has-phases", "--strict-two-level"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = json.loads(proc.stdout)
            self.assertTrue(out["passed"], out["fails"])
            # The two-level info line appears because strict implies two-level.
            self.assertTrue(
                any("two-level hierarchy detected" in i for i in out["info"]),
                out["info"],
            )
            self.assertTrue(
                any("strict citation-walk" in i for i in out["info"]),
                out["info"],
            )


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
