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


class MetaSkillExceptionTests(unittest.TestCase):
    """Stage 10c: BP-003 meta-skill exception. Skills with `meta-skill: true`
    in frontmatter skip Check 14. CLI `--meta-skill` flag forces the skip
    regardless of frontmatter (used for testing client fixtures + bonus
    sweeps). The default (no marker, no flag) runs Check 14 normally.
    """

    def test_is_meta_skill_returns_true_on_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "fake"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\n"
                "meta-skill: true\n"
                "name: fake-meta\n"
                "description: A fake meta-skill.\n"
                "---\n\n# fake-meta\n",
                encoding="utf-8",
            )
            self.assertTrue(gate.is_meta_skill(skill))

    def test_is_meta_skill_returns_false_without_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "fake"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: fake-client\ndescription: A client.\n---\n",
                encoding="utf-8",
            )
            self.assertFalse(gate.is_meta_skill(skill))

    def test_is_meta_skill_returns_false_on_meta_skill_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "fake"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nmeta-skill: false\nname: fake\ndescription: x.\n---\n",
                encoding="utf-8",
            )
            self.assertFalse(gate.is_meta_skill(skill))

    def test_is_meta_skill_handles_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(gate.is_meta_skill(Path(tmp)))

    def test_is_meta_skill_handles_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "fake"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "# fake\n\nNo frontmatter here.\n", encoding="utf-8"
            )
            self.assertFalse(gate.is_meta_skill(skill))

    def test_evaluate_skips_check_14_when_meta_skill_in_frontmatter(self):
        """Loading the failing-meta-cite fixture but adding the marker."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # Copy fixture to a temp dir so we can mutate frontmatter
            src = FIXTURES / "failing-meta-cite"
            dst = tmp / "skill"
            dst.mkdir()
            (dst / "SKILL.md").write_text(
                "---\n"
                "meta-skill: true\n"
                "name: skill-compliance\n"
                "description: A fake meta-skill that legitimately cites bp-028.\n"
                "---\n\n# skill-compliance\n",
                encoding="utf-8",
            )
            (dst / "references").mkdir()
            (dst / "references" / "bad.md").write_text(
                "See bp-028 and patterns/meta/bp-028.\n",
                encoding="utf-8",
            )
            verdict = gate.evaluate(dst)
            self.assertTrue(verdict.get("meta_skill"))
            self.assertEqual(verdict["check_14_hits"], [])
            # Check 14 skipped → no Check-14-driven failure.
            self.assertEqual(verdict["verdict"], "pass")

    def test_evaluate_explicit_meta_skill_true_overrides_frontmatter(self):
        """The `meta_skill=True` arg forces meta-skill mode even when the
        frontmatter has no marker. Used by `--meta-skill` CLI flag."""
        verdict = gate.evaluate(
            FIXTURES / "failing-meta-cite", meta_skill=True
        )
        self.assertTrue(verdict.get("meta_skill"))
        self.assertEqual(verdict["check_14_hits"], [])
        self.assertEqual(verdict["verdict"], "pass")

    def test_evaluate_explicit_meta_skill_false_overrides_frontmatter(self):
        """The `meta_skill=False` arg forces client-skill mode (run Check 14)
        even when the frontmatter says `meta-skill: true`."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            dst = tmp / "skill"
            dst.mkdir()
            # Marker says meta-skill, but caller forces False.
            (dst / "SKILL.md").write_text(
                "---\n"
                "meta-skill: true\n"
                "name: fake-meta\n"
                "description: x.\n"
                "---\n",
                encoding="utf-8",
            )
            (dst / "references").mkdir()
            (dst / "references" / "bad.md").write_text(
                "See bp-028.\n", encoding="utf-8"
            )
            verdict = gate.evaluate(dst, meta_skill=False)
            self.assertFalse(verdict.get("meta_skill"))
            self.assertGreaterEqual(len(verdict["check_14_hits"]), 1)
            self.assertEqual(verdict["verdict"], "fail")

    def test_cli_meta_skill_flag_makes_meta_cite_fixture_pass(self):
        """End-to-end CLI: --meta-skill flag flips fixture from FAIL to PASS."""
        # Without flag → fail
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "failing-meta-cite")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        # With flag → pass
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "failing-meta-cite"),
             "--meta-skill"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "pass")
        self.assertTrue(parsed["meta_skill"])

    def test_verdict_includes_meta_skill_field(self):
        """The verdict dict always carries `meta_skill` for auditability —
        even on PASS where Check 14 hits would have been zero anyway."""
        verdict = gate.evaluate(FIXTURES / "passing")
        self.assertIn("meta_skill", verdict)
        self.assertIsInstance(verdict["meta_skill"], bool)


class Stage13ConstantsTests(unittest.TestCase):
    """Locks the BP033_PHASE_SUBSKILL_SLUGS + FACTORY_INTERNAL_SLUGS sets
    so a future addition or removal forces an explicit test edit."""

    def test_phase_subskill_slugs_are_the_six_pack_consumers(self):
        self.assertEqual(
            gate.BP033_PHASE_SUBSKILL_SLUGS,
            frozenset({
                "skill-frontmatter",
                "skill-phase-designer",
                "skill-references-scaffolder",
                "skill-cron-observability",
                "skill-signed-handoff",
                "skill-compliance-gate",
            }),
        )

    def test_factory_internal_allowlist_is_phase_subskills_plus_three(self):
        extras = gate.FACTORY_INTERNAL_SLUGS - gate.BP033_PHASE_SUBSKILL_SLUGS
        self.assertEqual(
            extras,
            frozenset({"skill-factory", "skill-compliance",
                       "skill-spec-validator"}),
        )

    def test_factory_internal_allowlist_count_is_nine(self):
        self.assertEqual(len(gate.FACTORY_INTERNAL_SLUGS), 9)

    def test_phase_subskills_subset_of_factory_internal(self):
        self.assertTrue(
            gate.BP033_PHASE_SUBSKILL_SLUGS.issubset(
                gate.FACTORY_INTERNAL_SLUGS
            )
        )


class BP033PreamblePatternTests(unittest.TestCase):
    """The Signal 1 regex must match canonical preambles and reject text
    that mentions only one half of the pair."""

    def test_canonical_preamble_matches(self):
        text = "**Read ONLY your `phases/01-frontmatter/input.md`** per BP-033."
        self.assertIsNotNone(gate.BP033_PREAMBLE_PATTERN.search(text))

    def test_case_insensitive(self):
        text = "read only the input.md pack."
        self.assertIsNotNone(gate.BP033_PREAMBLE_PATTERN.search(text))

    def test_only_read_only_does_not_match(self):
        self.assertIsNone(gate.BP033_PREAMBLE_PATTERN.search("Read ONLY"))

    def test_only_input_md_does_not_match(self):
        self.assertIsNone(
            gate.BP033_PREAMBLE_PATTERN.search("see input.md for details")
        )

    def test_pair_split_across_lines_does_not_match(self):
        # Single-line constraint: [^\n] in the regex.
        text = "Read ONLY here\n\nlater: input.md elsewhere"
        self.assertIsNone(gate.BP033_PREAMBLE_PATTERN.search(text))


class BP033PatternsPathTests(unittest.TestCase):
    """The Signal 2 regex must catch concrete patterns/bp-NNN-name.md
    references but explicitly NOT match the template form `bp-NNN-*.md`
    (literal NNN letters) used by sub-skills to describe the input contract.
    """

    def test_concrete_top_level_path_matches(self):
        self.assertIsNotNone(
            gate.BP033_PATTERNS_PATH.search("see patterns/bp-007-references.md")
        )

    def test_concrete_meta_path_matches(self):
        self.assertIsNotNone(
            gate.BP033_PATTERNS_PATH.search(
                "patterns/meta/bp-033-driver-context-packs.md"
            )
        )

    def test_template_form_does_not_match(self):
        # This is the critical false-positive guard: every phase sub-skill
        # describes the pack contract with this template form.
        self.assertIsNone(
            gate.BP033_PATTERNS_PATH.search(
                "for each `patterns/bp-NNN-*.md` listed under BPs to enforce"
            )
        )

    def test_template_meta_form_does_not_match(self):
        self.assertIsNone(
            gate.BP033_PATTERNS_PATH.search("patterns/meta/bp-NNN-name.md")
        )

    def test_match_is_case_insensitive(self):
        self.assertIsNotNone(
            gate.BP033_PATTERNS_PATH.search("PATTERNS/BP-007-REFERENCES.MD")
        )

    def test_match_requires_dot_md_suffix(self):
        # A path that looks like a directory but lacks .md should not match.
        self.assertIsNone(
            gate.BP033_PATTERNS_PATH.search("patterns/bp-007/")
        )


class ReadSkillNameTests(unittest.TestCase):
    def test_returns_name_from_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: skill-frontmatter\ndescription: x.\n---\n",
                encoding="utf-8",
            )
            self.assertEqual(gate._read_skill_name(skill), "skill-frontmatter")

    def test_strips_quotes_and_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname:   'skill-x'  \ndescription: x.\n---\n",
                encoding="utf-8",
            )
            self.assertEqual(gate._read_skill_name(skill), "skill-x")

    def test_returns_none_on_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(gate._read_skill_name(Path(tmp)))

    def test_returns_none_on_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# no frontmatter\n",
                                            encoding="utf-8")
            self.assertIsNone(gate._read_skill_name(skill))

    def test_returns_none_on_missing_name_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\ndescription: no name here.\n---\n",
                encoding="utf-8",
            )
            self.assertIsNone(gate._read_skill_name(skill))


class Check15BP033LeakageFixtureTests(unittest.TestCase):
    """Stage 13 Check 15 — fixture-driven verdicts."""

    def test_pass_fixture_reports_checked_and_clean(self):
        v = gate.evaluate(FIXTURES / "check15-pass-frontmatter")
        self.assertEqual(v["verdict"], "pass")
        self.assertTrue(v["bp033_leakage"]["checked"])
        self.assertEqual(v["bp033_leakage"]["slug"], "skill-frontmatter")
        self.assertFalse(v["bp033_leakage"]["missing_preamble"])
        self.assertEqual(v["bp033_leakage"]["hits"], [])

    def test_no_preamble_fixture_fails_with_missing_preamble(self):
        v = gate.evaluate(FIXTURES / "check15-fail-no-preamble")
        self.assertEqual(v["verdict"], "fail")
        self.assertTrue(v["bp033_leakage"]["checked"])
        self.assertTrue(v["bp033_leakage"]["missing_preamble"])
        self.assertEqual(v["bp033_leakage"]["hits"], [])
        self.assertIn("Check 15: BP-033 preamble missing", v["blocker"])

    def test_direct_read_fixture_fails_with_hit(self):
        v = gate.evaluate(FIXTURES / "check15-fail-direct-read")
        self.assertEqual(v["verdict"], "fail")
        self.assertTrue(v["bp033_leakage"]["checked"])
        self.assertFalse(v["bp033_leakage"]["missing_preamble"])
        self.assertEqual(len(v["bp033_leakage"]["hits"]), 1)
        hit = v["bp033_leakage"]["hits"][0]
        self.assertEqual(hit["file"], "references/leaky.md")
        self.assertEqual(hit["matched"], "patterns/bp-007-references.md")
        self.assertGreater(hit["line"], 0)
        self.assertIn("Check 15:", v["blocker"])
        self.assertIn("patterns/bp-007-references.md", v["blocker"])

    def test_non_subskill_slug_skips_check_15(self):
        v = gate.evaluate(FIXTURES / "check15-skip-non-subskill")
        self.assertEqual(v["verdict"], "pass")
        self.assertFalse(v["bp033_leakage"]["checked"])
        self.assertEqual(v["bp033_leakage"]["slug"], "skill-factory")

    def test_client_skill_without_marker_skips_check_15(self):
        # Reuses the existing passing fixture: no meta-skill marker, so
        # slug isn't even read for the BP-033 check; fast-path skip.
        v = gate.evaluate(FIXTURES / "passing")
        self.assertFalse(v["bp033_leakage"]["checked"])


class Check15UnitTests(unittest.TestCase):
    """Direct unit tests for check_15_bp033_leakage on synthetic dirs."""

    def _mk(self, tmp: Path, slug: str, body: str,
            extra_files: dict | None = None) -> Path:
        skill = tmp / "s"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: x.\n---\n\n{body}\n",
            encoding="utf-8",
        )
        if extra_files:
            for relpath, content in extra_files.items():
                p = skill / relpath
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        return skill

    def test_skip_when_slug_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._mk(Path(tmp), "totally-unknown-slug",
                             "Read ONLY input.md.")
            r = gate.check_15_bp033_leakage(skill)
            self.assertFalse(r["checked"])
            self.assertEqual(r["slug"], "totally-unknown-slug")

    def test_skip_when_slug_is_driver(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._mk(Path(tmp), "skill-factory",
                             "no preamble here")
            r = gate.check_15_bp033_leakage(skill)
            self.assertFalse(r["checked"])

    def test_runs_and_passes_on_phase_subskill_with_clean_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._mk(Path(tmp), "skill-phase-designer",
                             "Read ONLY your input.md pack.")
            r = gate.check_15_bp033_leakage(skill)
            self.assertTrue(r["checked"])
            self.assertFalse(r["missing_preamble"])
            self.assertEqual(r["hits"], [])

    def test_runs_and_fails_on_missing_preamble(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._mk(Path(tmp), "skill-phase-designer",
                             "no preamble at all")
            r = gate.check_15_bp033_leakage(skill)
            self.assertTrue(r["checked"])
            self.assertTrue(r["missing_preamble"])

    def test_scan_covers_phase_director_files(self):
        # Hits in phases/<n>/director.md are reported with the relative path.
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._mk(
                Path(tmp), "skill-phase-designer",
                "Read ONLY your input.md pack.",
                extra_files={
                    "phases/01-foo/director.md":
                        "see patterns/bp-009-references.md for details\n",
                },
            )
            r = gate.check_15_bp033_leakage(skill)
            self.assertTrue(r["checked"])
            self.assertEqual(len(r["hits"]), 1)
            self.assertEqual(r["hits"][0]["file"],
                             "phases/01-foo/director.md")


class Check16CrossScopeFixtureTests(unittest.TestCase):
    """Stage 13 Check 16 — fixture-driven verdicts."""

    def test_leaked_fixture_fails_with_cross_scope(self):
        v = gate.evaluate(FIXTURES / "check16-fail-leaked")
        self.assertEqual(v["verdict"], "fail")
        self.assertTrue(v["cross_scope_meta"]["checked"])
        self.assertTrue(v["cross_scope_meta"]["leaked"])
        self.assertEqual(v["cross_scope_meta"]["slug"], "acme-board-memo")
        self.assertIn("Check 16:", v["blocker"])
        self.assertIn("acme-board-memo", v["blocker"])

    def test_factory_internal_slug_with_marker_does_not_leak(self):
        v = gate.evaluate(FIXTURES / "check15-skip-non-subskill")
        # slug is "skill-factory" with meta-skill: true → in allowlist.
        self.assertTrue(v["cross_scope_meta"]["checked"])
        self.assertFalse(v["cross_scope_meta"]["leaked"])

    def test_no_marker_skips_check_16(self):
        v = gate.evaluate(FIXTURES / "passing")
        self.assertFalse(v["cross_scope_meta"]["checked"])
        self.assertFalse(v["cross_scope_meta"]["leaked"])


class Check16UnitTests(unittest.TestCase):
    def test_returns_skip_when_not_meta(self):
        r = gate.check_16_cross_scope_meta_skill(Path("/tmp"), is_meta=False)
        self.assertFalse(r["checked"])
        self.assertFalse(r["leaked"])

    def test_leaked_true_when_slug_outside_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: some-client-skill\ndescription: x.\n---\n",
                encoding="utf-8",
            )
            r = gate.check_16_cross_scope_meta_skill(skill, is_meta=True)
            self.assertTrue(r["checked"])
            self.assertTrue(r["leaked"])
            self.assertEqual(r["slug"], "some-client-skill")

    def test_leaked_false_when_slug_in_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            for slug in ("skill-factory", "skill-frontmatter",
                         "skill-spec-validator"):
                skill = Path(tmp) / slug
                skill.mkdir()
                (skill / "SKILL.md").write_text(
                    f"---\nname: {slug}\ndescription: x.\n---\n",
                    encoding="utf-8",
                )
                r = gate.check_16_cross_scope_meta_skill(skill, is_meta=True)
                with self.subTest(slug=slug):
                    self.assertTrue(r["checked"])
                    self.assertFalse(r["leaked"])


class Stage13VerdictShapeTests(unittest.TestCase):
    """The verdict dict gains two new keys; all early-return paths must
    populate them so callers can rely on the schema."""

    def test_pass_verdict_has_new_keys(self):
        v = gate.evaluate(FIXTURES / "passing")
        self.assertIn("bp033_leakage", v)
        self.assertIn("cross_scope_meta", v)
        self.assertIsInstance(v["bp033_leakage"], dict)
        self.assertIsInstance(v["cross_scope_meta"], dict)

    def test_missing_skill_dir_verdict_has_new_keys(self):
        v = gate.evaluate(Path("/nonexistent/skill"))
        self.assertEqual(v["verdict"], "fail")
        self.assertIn("bp033_leakage", v)
        self.assertIn("cross_scope_meta", v)

    def test_missing_compliance_check_verdict_has_new_keys(self):
        with mock.patch.object(
            gate, "COMPLIANCE_CHECK_PATH",
            Path("/nonexistent/compliance_check.py"),
        ):
            v = gate.evaluate(FIXTURES / "passing")
        self.assertEqual(v["verdict"], "fail")
        self.assertIn("bp033_leakage", v)
        self.assertIn("cross_scope_meta", v)


class Stage13DriverModeAndCliTests(unittest.TestCase):
    """End-to-end CLI + driver-mode tests for the new check pair."""

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

    def test_driver_mode_writes_blocker_for_check_15_direct_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_md = self._write_input(
                Path(tmp), FIXTURES / "check15-fail-direct-read"
            )
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 1)
            line = (input_md.parent / "notes.md").read_text(encoding="utf-8")
            self.assertTrue(line.startswith("BLOCKER: compliance gate failed"))
            self.assertIn("Check 15", line)

    def test_driver_mode_writes_blocker_for_check_16_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_md = self._write_input(
                Path(tmp), FIXTURES / "check16-fail-leaked"
            )
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 1)
            line = (input_md.parent / "notes.md").read_text(encoding="utf-8")
            self.assertIn("Check 16", line)
            self.assertIn("acme-board-memo", line)

    def test_cli_exits_1_on_check_15_fail(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "check15-fail-direct-read")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "fail")
        self.assertEqual(len(parsed["bp033_leakage"]["hits"]), 1)

    def test_cli_exits_1_on_check_16_fail(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "check16-fail-leaked")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "fail")
        self.assertTrue(parsed["cross_scope_meta"]["leaked"])

    def test_cli_exits_0_on_check_15_pass_fixture(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "gate.py"),
             "--skill", str(FIXTURES / "check15-pass-frontmatter")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["verdict"], "pass")
        self.assertTrue(parsed["bp033_leakage"]["checked"])

    def test_pass_output_md_includes_check_15_and_16_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_md = self._write_input(
                Path(tmp), FIXTURES / "check15-pass-frontmatter"
            )
            rc = gate.main_driver(input_md)
            self.assertEqual(rc, 0)
            body = (input_md.parent / "output.md").read_text(encoding="utf-8")
            self.assertIn("Check 15", body)
            self.assertIn("Check 16", body)


if __name__ == "__main__":
    unittest.main()
