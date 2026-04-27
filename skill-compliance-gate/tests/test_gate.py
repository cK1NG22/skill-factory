"""Unit tests for skill-compliance-gate/scripts/gate.py.

Run from skill-compliance-gate/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
FIXTURES = REPO_SKILL / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import gate  # noqa: E402


class ParseInputMdTests(unittest.TestCase):
    def test_parses_double_star_key_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.md"
            p.write_text(
                "# pack\n"
                "- **assembled_skill_path**: /tmp/foo\n"
                "- **work_dir**: /tmp/bar\n",
                encoding="utf-8",
            )
            self.assertEqual(
                gate.parse_input_md(p),
                {"assembled_skill_path": "/tmp/foo", "work_dir": "/tmp/bar"},
            )

    def test_missing_file_returns_empty(self):
        self.assertEqual(gate.parse_input_md(Path("/nonexistent/xx")), {})

    def test_strips_backticks_and_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.md"
            p.write_text("**assembled_skill_path**: `/abs/path`\n", encoding="utf-8")
            self.assertEqual(
                gate.parse_input_md(p), {"assembled_skill_path": "/abs/path"}
            )


class MetaBPPatternTests(unittest.TestCase):
    """Exercise the Check 14 regex across the full 11-slug matrix + edges."""

    POSITIVE_SLUGS = [
        "bp-018", "bp-025", "bp-026", "bp-027", "bp-028",
        "bp-029", "bp-030", "bp-031", "bp-032", "bp-033", "bp-034",
    ]

    def test_every_meta_slug_matches(self):
        for slug in self.POSITIVE_SLUGS:
            with self.subTest(slug=slug):
                self.assertIsNotNone(gate.META_BP_PATTERN.search(f"see {slug} for details"))

    def test_non_meta_slugs_do_not_match(self):
        for slug in ["bp-001", "bp-007", "bp-008", "bp-009", "bp-024"]:
            with self.subTest(slug=slug):
                self.assertIsNone(gate.META_BP_PATTERN.search(f"see {slug} for details"))

    def test_case_insensitive_match(self):
        self.assertIsNotNone(gate.META_BP_PATTERN.search("BP-028"))

    def test_slug_in_fenced_code_block_still_matches(self):
        """Per gate-contract.md §Family 2: inline code wrapping does not
        excuse a client skill from the meta-cite ban.
        """
        text = "```\nsee `bp-028` for details\n```"
        self.assertIsNotNone(gate.META_BP_PATTERN.search(text))

    def test_path_form_matches(self):
        self.assertIsNotNone(
            gate.META_BP_PATTERN.search("patterns/meta/bp-099-made-up.md")
        )

    def test_slug_without_word_boundary_does_not_match(self):
        # "xbp-028" should not match because of `\b` at the start.
        self.assertIsNone(gate.META_BP_PATTERN.search("xbp-028"))


class CollectScanFilesTests(unittest.TestCase):
    def test_scans_skill_md_refs_phases_phase_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text("x", encoding="utf-8")
            (skill / "references").mkdir()
            (skill / "references" / "a.md").write_text("x", encoding="utf-8")
            (skill / "references" / "sub").mkdir()
            # Nested subdirs under references/ must NOT be scanned.
            (skill / "references" / "sub" / "deep.md").write_text("x", encoding="utf-8")
            (skill / "phases" / "01-foo").mkdir(parents=True)
            (skill / "phases" / "01-foo" / "director.md").write_text("x", encoding="utf-8")
            (skill / "phases" / "01-foo" / "references").mkdir()
            (skill / "phases" / "01-foo" / "references" / "b.md").write_text("x", encoding="utf-8")
            files = {str(p.relative_to(skill)) for p in gate.collect_scan_files(skill)}
            self.assertIn("SKILL.md", files)
            self.assertIn("references/a.md", files)
            self.assertIn("phases/01-foo/director.md", files)
            self.assertIn("phases/01-foo/references/b.md", files)
            # Nested subdir under references/ should be absent.
            self.assertNotIn("references/sub/deep.md", files)

    def test_scripts_and_fixtures_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text("x", encoding="utf-8")
            (skill / "scripts").mkdir()
            (skill / "scripts" / "t.py").write_text("bp-028", encoding="utf-8")
            (skill / "fixtures").mkdir()
            (skill / "fixtures" / "a.md").write_text("bp-028", encoding="utf-8")
            files = {str(p.relative_to(skill)) for p in gate.collect_scan_files(skill)}
            self.assertNotIn("scripts/t.py", files)
            self.assertNotIn("fixtures/a.md", files)


class EvaluatePassingFixtureTests(unittest.TestCase):
    def test_passing_fixture_verdict_pass(self):
        v = gate.evaluate(FIXTURES / "passing")
        self.assertEqual(v["verdict"], "pass")
        self.assertEqual(v["checker_fails"], [])
        self.assertEqual(v["check_14_hits"], [])


class EvaluateFailingRequiredTests(unittest.TestCase):
    def test_failing_required_has_checker_fail(self):
        v = gate.evaluate(FIXTURES / "failing-required")
        self.assertEqual(v["verdict"], "fail")
        self.assertGreaterEqual(len(v["checker_fails"]), 1)
        ids = {f["id"] for f in v["checker_fails"]}
        self.assertIn(4, ids)  # description_exists

    def test_blocker_line_format_required(self):
        v = gate.evaluate(FIXTURES / "failing-required")
        self.assertTrue(v["blocker"].startswith("compliance gate failed"))
        self.assertIn("required-tier", v["blocker"])


class EvaluateFailingMetaCiteTests(unittest.TestCase):
    def test_failing_meta_cite_has_check14_hits(self):
        v = gate.evaluate(FIXTURES / "failing-meta-cite")
        self.assertEqual(v["verdict"], "fail")
        self.assertEqual(v["checker_fails"], [])
        self.assertGreaterEqual(len(v["check_14_hits"]), 1)

    def test_check14_hit_records_file_and_line(self):
        v = gate.evaluate(FIXTURES / "failing-meta-cite")
        hit = v["check_14_hits"][0]
        self.assertEqual(hit["file"], "references/bad-citation.md")
        self.assertIsInstance(hit["line"], int)
        self.assertGreater(hit["line"], 0)


class MissingCheckerCorePreconditionTests(unittest.TestCase):
    def test_missing_compliance_check_py_yields_blocker(self):
        with mock.patch.object(gate, "COMPLIANCE_CHECK_PATH", Path("/nonexistent/compliance_check.py")):
            v = gate.evaluate(FIXTURES / "passing")
        self.assertEqual(v["verdict"], "fail")
        self.assertIn("skill-compliance not installed at", v["blocker"])


class MissingAssembledSkillPathTests(unittest.TestCase):
    def test_nonexistent_skill_path_yields_blocker(self):
        v = gate.evaluate(Path("/nonexistent/skill"))
        self.assertEqual(v["verdict"], "fail")
        self.assertIn("assembled skill not found at", v["blocker"])


class DriverModeTests(unittest.TestCase):
    def _write_input(self, tmp: Path, assembled: Path) -> Path:
        phase_dir = tmp / "phases" / "08-assemble-and-gate"
        phase_dir.mkdir(parents=True)
        input_md = phase_dir / "input.md"
        input_md.write_text(
            f"- **assembled_skill_path**: {assembled}\n"
            f"- **work_dir**: {tmp}\n",
            encoding="utf-8",
        )
        return input_md

    def test_driver_mode_writes_output_md_on_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_md = self._write_input(Path(tmp), FIXTURES / "passing")
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 0)
            self.assertTrue((input_md.parent / "output.md").exists())
            self.assertFalse((input_md.parent / "notes.md").exists())
            body = (input_md.parent / "output.md").read_text(encoding="utf-8")
            self.assertIn("PASS", body)
            self.assertIn("Gate verdict", body)

    def test_driver_mode_writes_notes_md_on_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_md = self._write_input(Path(tmp), FIXTURES / "failing-required")
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 1)
            self.assertTrue((input_md.parent / "notes.md").exists())
            line = (input_md.parent / "notes.md").read_text(encoding="utf-8")
            self.assertTrue(line.startswith("BLOCKER: compliance gate failed"))

    def test_driver_mode_malformed_input_yields_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp) / "phases" / "08-assemble-and-gate"
            phase_dir.mkdir(parents=True)
            input_md = phase_dir / "input.md"
            input_md.write_text("no fields here\n", encoding="utf-8")
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 1)
            line = (phase_dir / "notes.md").read_text(encoding="utf-8")
            self.assertIn("assembled_skill_path missing", line)


class StandaloneCliSmokeTests(unittest.TestCase):
    def test_standalone_cli_exit_0_on_pass(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "passing")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "pass")

    def test_standalone_cli_exit_1_on_fail(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "failing-meta-cite")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "fail")
        self.assertGreaterEqual(len(parsed["check_14_hits"]), 1)


class SummaryTableTests(unittest.TestCase):
    def test_output_md_contains_counts_from_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp) / "phases" / "08-assemble-and-gate"
            phase_dir.mkdir(parents=True)
            input_md = phase_dir / "input.md"
            input_md.write_text(
                f"**assembled_skill_path**: {FIXTURES / 'passing'}\n"
                f"**work_dir**: {tmp}\n",
                encoding="utf-8",
            )
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 0)
            body = (phase_dir / "output.md").read_text(encoding="utf-8")
            # 12 passed / 0 warn / 0 fail / 1 info = canonical fixture row.
            self.assertRegex(body, r"\|\s*12\s*\|\s*0\s*\|\s*0\s*\|\s*1\s*\|")


if __name__ == "__main__":
    unittest.main()
