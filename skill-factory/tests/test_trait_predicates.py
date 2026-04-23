"""Unit tests for trait_predicates.py — exercises the 5 predicates + 4 edge cases.

Run from skill-factory/skill-factory/:
    python3 -m unittest tests.test_trait_predicates -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
FIXTURES = REPO_SKILL / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import trait_predicates as tp  # noqa: E402


def _make_mock_ecosystem(tmp: Path, skill_names: list[str]) -> Path:
    eco = tmp / "ecosystem"
    eco.mkdir()
    for name in skill_names:
        d = eco / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return eco


# ----------- Spec-mode tests -----------


class TestSpecMode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # Mock ecosystem: just /docx so phased-hitl-with-reuse can pass BP-034
        self.eco = _make_mock_ecosystem(self.tmp, ["docx"])

    def tearDown(self):
        self._tmp.cleanup()

    def _classify(self, fixture: str) -> dict:
        return tp.classify_spec(FIXTURES / "specs" / fixture, ecosystem=self.eco)

    def test_clean_transformation(self):
        r = self._classify("clean-transformation.md")["traits"]
        self.assertFalse(r["has_references"]["fires"])
        self.assertFalse(r["has_phases"]["fires"])
        self.assertFalse(r["has_hitl"]["fires"])
        self.assertFalse(r["is_scheduled"]["fires"])
        self.assertFalse(r["invokes_skills"]["fires"])

    def test_phased_hitl_with_reuse(self):
        r = self._classify("phased-hitl-with-reuse.md")["traits"]
        self.assertTrue(r["has_references"]["fires"], r["has_references"])
        self.assertTrue(r["has_phases"]["fires"], r["has_phases"])
        self.assertTrue(r["has_hitl"]["fires"], r["has_hitl"])
        self.assertFalse(r["is_scheduled"]["fires"], r["is_scheduled"])
        self.assertTrue(r["invokes_skills"]["fires"], r["invokes_skills"])
        self.assertIn("docx", r["invokes_skills"]["evidence"])

    def test_scheduled_report(self):
        r = self._classify("scheduled-report.md")["traits"]
        self.assertFalse(r["has_references"]["fires"])
        self.assertTrue(r["has_phases"]["fires"], r["has_phases"])
        self.assertFalse(r["has_hitl"]["fires"])
        self.assertTrue(r["is_scheduled"]["fires"], r["is_scheduled"])
        self.assertFalse(r["invokes_skills"]["fires"])

    def test_invokes_skills_rejects_nonexistent(self):
        # Even if the spec names /frobnicate, it should not fire because the
        # ecosystem check fails (BP-034 gate).
        spec = self.tmp / "bad-reuse.md"
        spec.write_text(
            "## Existing skills to reuse\n- /frobnicate\n", encoding="utf-8"
        )
        r = tp.classify_spec(spec, ecosystem=self.eco)["traits"]
        self.assertFalse(r["invokes_skills"]["fires"])
        self.assertIn("frobnicate", r["invokes_skills"]["evidence"])


# ----------- Skill-mode tests (edge cases 1–4) -----------


class TestEdgeCase1SiblingRefs(unittest.TestCase):
    def test_sibling_md_fires_has_references(self):
        skill = FIXTURES / "skills" / "sibling-refs-skill"
        r = tp.classify_skill(skill)["traits"]
        self.assertTrue(r["has_references"]["fires"], r["has_references"])
        self.assertIn("editing.md", r["has_references"]["evidence"])


class TestEdgeCase2WorkflowSection(unittest.TestCase):
    def test_workflow_heading_fires_has_phases(self):
        skill = FIXTURES / "skills" / "workflow-section-skill"
        r = tp.classify_skill(skill)["traits"]
        self.assertTrue(r["has_phases"]["fires"], r["has_phases"])
        self.assertIn("Workflow", r["has_phases"]["evidence"])


class TestEdgeCase3GstackPreamble(unittest.TestCase):
    def test_preamble_does_not_trigger_invokes_skills(self):
        # Even if the ecosystem has /gstack and /bin, the preamble strip should
        # prevent invokes_skills from firing for this fixture.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            eco = _make_mock_ecosystem(tmp_path, ["gstack", "dispatch"])
            skill = FIXTURES / "skills" / "gstack-preamble-skill"
            r = tp.classify_skill(skill, ecosystem=eco)["traits"]
            self.assertFalse(
                r["invokes_skills"]["fires"],
                f"preamble leaked: {r['invokes_skills']}",
            )


class TestEdgeCase4PairedToggle(unittest.TestCase):
    def test_paired_family_excluded_from_invokes_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Include /unfreeze in the mock ecosystem so we know it's the
            # blocklist (not the existence check) doing the work.
            eco = _make_mock_ecosystem(Path(tmp), ["unfreeze"])
            skill = FIXTURES / "skills" / "paired-toggle-skill"
            r = tp.classify_skill(skill, ecosystem=eco)["traits"]
            self.assertFalse(
                r["invokes_skills"]["fires"],
                f"paired family not excluded: {r['invokes_skills']}",
            )


# ----------- CLI integration test -----------


class TestCLI(unittest.TestCase):
    def test_cli_spec_mode_returns_json(self):
        spec = FIXTURES / "specs" / "clean-transformation.md"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "trait_predicates.py"), "spec", str(spec)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "spec")
        self.assertIn("traits", data)
        for trait in ("has_references", "has_phases", "has_hitl", "is_scheduled", "invokes_skills"):
            self.assertIn(trait, data["traits"])
            self.assertIn("fires", data["traits"][trait])
            self.assertIn("evidence", data["traits"][trait])

    def test_cli_bad_usage_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "trait_predicates.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
