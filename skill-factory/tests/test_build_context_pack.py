"""Unit tests for build_context_pack.py.

Run from skill-factory/:
    python3 -m unittest tests.test_build_context_pack -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_SKILL / "scripts"
PATTERNS_ROOT = REPO_SKILL.parent / "patterns"
ASSETS = REPO_SKILL.parent / "assets"
FIXTURES = REPO_SKILL / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import build_context_pack as bcp  # noqa: E402
import trait_predicates as tp  # noqa: E402


# ---------- Section parser ----------


class TestParseSpecSections(unittest.TestCase):
    def test_splits_on_h2_headings(self):
        spec = textwrap.dedent("""
            # Title

            Preamble paragraph.

            ## Company
            acme

            ## Skill slug
            board-memo

            ## One-line description
            Does a thing.
        """).strip()
        sections = bcp.parse_spec_sections(spec)
        self.assertEqual(sections["Company"], "acme")
        self.assertEqual(sections["Skill slug"], "board-memo")
        self.assertEqual(sections["One-line description"], "Does a thing.")

    def test_preserves_multi_paragraph_bodies(self):
        spec = textwrap.dedent("""
            ## Failure modes
            - line one
            - line two

            - line three after blank
        """).strip()
        sections = bcp.parse_spec_sections(spec)
        self.assertIn("line one", sections["Failure modes"])
        self.assertIn("line three after blank", sections["Failure modes"])


# ---------- Reuse-block slug extractor ----------


class TestExtractInvokedSlugs(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(bcp.extract_invoked_slugs("None"), [])

    def test_empty_input(self):
        self.assertEqual(bcp.extract_invoked_slugs(None), [])
        self.assertEqual(bcp.extract_invoked_slugs(""), [])

    def test_extracts_slugs(self):
        block = "- `/docx` — for .docx output\n- `/csv-tools` — maybe\n"
        self.assertEqual(bcp.extract_invoked_slugs(block), ["csv-tools", "docx"])

    def test_dedupes(self):
        block = "- `/docx`\n- `/docx` (again)"
        self.assertEqual(bcp.extract_invoked_slugs(block), ["docx"])


# ---------- Traits block renderer ----------


class TestRenderTraitsBlock(unittest.TestCase):
    def _cls(self, **fires) -> dict:
        defaults = dict(
            has_references=False, has_phases=False, has_hitl=False,
            is_scheduled=False, invokes_skills=False,
        )
        defaults.update(fires)
        return {
            "traits": {
                k: {"fires": v, "evidence": "test"} for k, v in defaults.items()
            }
        }

    def test_all_false(self):
        out = bcp.render_traits_block(self._cls(), [])
        self.assertIn("has_references: false", out)
        self.assertIn("invokes_skills: false", out)
        # no nested "- /..." entries
        self.assertNotIn("  -", out)

    def test_invokes_skills_renders_bulleted_slugs(self):
        out = bcp.render_traits_block(
            self._cls(invokes_skills=True), ["docx", "csv-tools"]
        )
        self.assertIn("invokes_skills: true", out)
        self.assertIn("  - /docx", out)
        self.assertIn("  - /csv-tools", out)

    def test_order_is_canonical(self):
        out = bcp.render_traits_block(self._cls(), [])
        lines = [ln.split(":")[0] for ln in out.splitlines()]
        self.assertEqual(lines, [
            "has_references", "has_phases", "has_hitl",
            "is_scheduled", "invokes_skills",
        ])


# ---------- End-to-end: build pack from acme example ----------


class TestBuildPackAcmeExample(unittest.TestCase):
    """Round-trip: feed the bundled acme-board-memo spec through the classifier,
    then through the pack builder, and assert the output contains everything
    the skill-frontmatter sub-skill needs.
    """

    def setUp(self):
        self.spec = ASSETS / "client-spec-examples" / "acme-board-memo.md"
        self.assertTrue(self.spec.is_file(), self.spec)
        self.tmp = tempfile.mkdtemp()
        self.out_dir = Path(self.tmp) / "phases" / "01-skill-frontmatter"
        self.cls_json = Path(self.tmp) / "classifier.json"
        # Produce the classifier JSON exactly as the driver's Phase 2 would
        result = tp.classify_spec(self.spec)
        self.cls_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_builds_input_md(self):
        out = bcp.build_pack(
            spec_path=self.spec,
            classifier_path=self.cls_json,
            sub_skill_name="skill-frontmatter",
            out_dir=self.out_dir,
            patterns_root=PATTERNS_ROOT,
        )
        self.assertTrue(out.is_file(), out)
        text = out.read_text(encoding="utf-8")

        # Required top-level headings (match the passing-input.md oracle)
        for heading in (
            "# Input pack — skill-frontmatter",
            "## Task",
            "## Spec excerpt",
            "## Classified traits",
            "## BPs to enforce",
            "## Output locations",
        ):
            self.assertIn(heading, text, f"missing heading: {heading}")

        # Spec excerpt fields
        self.assertIn("### Company\nacme", text)
        self.assertIn("### Skill slug\nboard-memo", text)
        self.assertIn("### Trigger phrases", text)
        self.assertIn('"generate board memo"', text)

        # Traits block reflects classifier output on acme spec
        # (acme invokes /docx which exists in the ecosystem via real check —
        #  when running tests outside that ecosystem the classifier may mark
        #  invokes_skills=false; either way, the block renders)
        self.assertIn("has_references:", text)
        self.assertIn("has_phases:", text)
        self.assertIn("invokes_skills:", text)

        # BP paths
        for bp in ("bp-001", "bp-002", "bp-003", "bp-004", "bp-005"):
            self.assertIn(bp, text, f"missing BP: {bp}")

        # Output-locations blurb
        self.assertIn("output.yaml", text)
        self.assertIn("output.md", text)
        self.assertIn("notes.md", text)
        self.assertIn("Do NOT open `patterns/`", text)


# ---------- Negative cases ----------


class TestBuildPackNegative(unittest.TestCase):
    def _write(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")

    def test_unsupported_sub_skill_raises(self):
        tmp = Path(tempfile.mkdtemp())
        spec = tmp / "spec.md"
        self._write(spec, "# t\n\n## Company\nacme\n\n## Skill slug\nx\n\n"
                          "## One-line description\nd\n\n## Trigger phrases\n- \"a b\"\n")
        cls = tmp / "c.json"
        self._write(cls, json.dumps({"traits": {}}))
        with self.assertRaises(ValueError):
            bcp.build_pack(spec, cls, "skill-does-not-exist", tmp / "out", PATTERNS_ROOT)

    def test_missing_required_section_raises(self):
        tmp = Path(tempfile.mkdtemp())
        spec = tmp / "spec.md"
        self._write(spec, "# t\n\n## Company\nacme\n")  # missing Skill slug etc.
        cls = tmp / "c.json"
        self._write(cls, json.dumps({"traits": {}}))
        with self.assertRaises(ValueError) as ctx:
            bcp.build_pack(spec, cls, "skill-frontmatter", tmp / "out", PATTERNS_ROOT)
        self.assertIn("missing required section", str(ctx.exception))


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def test_cli_happy_path(self):
        spec = ASSETS / "client-spec-examples" / "acme-board-memo.md"
        tmp = Path(tempfile.mkdtemp())
        cls_json = tmp / "cls.json"
        out_dir = tmp / "phases" / "01-skill-frontmatter"
        cls_json.write_text(json.dumps(tp.classify_spec(spec), indent=2), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS / "build_context_pack.py"),
                str(spec), str(cls_json), "skill-frontmatter", str(out_dir),
                "--patterns-root", str(PATTERNS_ROOT),
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        self.assertTrue((out_dir / "input.md").is_file())

    def test_cli_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "build_context_pack.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


# ---------- skill-phase-designer registration (Stage 7b) ----------


class TestPhaseDesignerRegistration(unittest.TestCase):
    """Confirm `skill-phase-designer` plugs into all 4 registries and that
    trait-gated BPs / sections are unioned correctly based on `has_hitl`."""

    def test_all_four_registries_have_phase_designer(self):
        self.assertIn("skill-phase-designer", bcp._SUB_SKILL_BPS)
        self.assertIn("skill-phase-designer", bcp._SUB_SKILL_SECTIONS)
        self.assertIn("skill-phase-designer", bcp._SUB_SKILL_OUTPUT_BLURB)
        self.assertIn("skill-phase-designer", bcp._SUB_SKILL_TASK)

    def test_base_bp_list_is_bp010_only(self):
        self.assertEqual(
            bcp._SUB_SKILL_BPS["skill-phase-designer"],
            ["bp-010-apply-once-carry-forward.md"],
        )

    def test_resolve_bps_no_hitl_yields_only_bp010(self):
        paths = bcp.resolve_bp_paths(
            "skill-phase-designer", PATTERNS_ROOT,
            firing_traits=["has_phases", "invokes_skills"],
        )
        self.assertEqual(len(paths), 1)
        self.assertTrue(paths[0].endswith("bp-010-apply-once-carry-forward.md"))

    def test_resolve_bps_with_hitl_yields_all_six(self):
        paths = bcp.resolve_bp_paths(
            "skill-phase-designer", PATTERNS_ROOT,
            firing_traits=["has_phases", "has_hitl", "invokes_skills"],
        )
        self.assertEqual(len(paths), 6)
        basenames = [Path(p).name for p in paths]
        self.assertEqual(basenames, [
            "bp-010-apply-once-carry-forward.md",
            "bp-011-announce-phase-transitions.md",
            "bp-012-hard-gates.md",
            "bp-013-ask-user-first.md",
            "bp-015-number-questions.md",
            "bp-016-inline-question-rule.md",
        ])


class TestPhaseDesignerPackNoHitl(unittest.TestCase):
    """Build a pack for the acme-board-memo spec (has_phases=true,
    has_hitl=false). Expect only BP-010 and the base section set."""

    def setUp(self):
        self.spec = ASSETS / "client-spec-examples" / "acme-board-memo.md"
        self.tmp = tempfile.mkdtemp()
        self.out_dir = Path(self.tmp) / "phases" / "02-skill-phase-designer"
        self.cls_json = Path(self.tmp) / "classifier.json"
        self.cls_json.write_text(
            json.dumps(tp.classify_spec(self.spec), indent=2), encoding="utf-8"
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_pack_has_only_bp010_when_no_hitl(self):
        out = bcp.build_pack(
            spec_path=self.spec,
            classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir,
            patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        self.assertIn("bp-010-apply-once-carry-forward.md", text)
        for absent_bp in ("bp-011", "bp-012", "bp-013", "bp-015", "bp-016"):
            self.assertNotIn(absent_bp, text, f"unexpected BP in no-HITL pack: {absent_bp}")

    def test_pack_contains_happy_path_walkthrough(self):
        out = bcp.build_pack(
            spec_path=self.spec, classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir, patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        self.assertIn("### Happy-path walkthrough", text)
        self.assertIn("Read the input `.md` file", text)

    def test_pack_contains_failure_modes_and_reuse(self):
        out = bcp.build_pack(
            spec_path=self.spec, classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir, patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        self.assertIn("### Failure modes", text)
        self.assertIn("### Existing skills to reuse", text)
        # /docx named in the reuse section + surfaced under invokes_skills
        self.assertIn("/docx", text)

    def test_pack_output_blurb_points_to_phase_02_dir(self):
        out = bcp.build_pack(
            spec_path=self.spec, classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir, patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        self.assertIn("phases/02-skill-phase-designer/", text)
        self.assertIn("output.md", text)
        self.assertIn("notes.md", text)


class TestPhaseDesignerPackHitl(unittest.TestCase):
    """Build a pack for the phased-hitl-with-reuse fixture
    (has_phases=true, has_hitl=true). Expect all 6 BPs."""

    def setUp(self):
        self.spec = FIXTURES / "specs" / "phased-hitl-with-reuse.md"
        self.assertTrue(self.spec.is_file(), self.spec)
        self.tmp = tempfile.mkdtemp()
        self.out_dir = Path(self.tmp) / "phases" / "02-skill-phase-designer"
        self.cls_json = Path(self.tmp) / "classifier.json"
        self.cls_json.write_text(
            json.dumps(tp.classify_spec(self.spec), indent=2), encoding="utf-8"
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_pack_has_all_six_bps_when_hitl_fires(self):
        out = bcp.build_pack(
            spec_path=self.spec, classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir, patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        for bp in ("bp-010", "bp-011", "bp-012", "bp-013", "bp-015", "bp-016"):
            self.assertIn(bp, text, f"missing BP in HITL pack: {bp}")

    def test_hitl_pack_traits_block_shows_has_hitl_true(self):
        out = bcp.build_pack(
            spec_path=self.spec, classifier_path=self.cls_json,
            sub_skill_name="skill-phase-designer",
            out_dir=self.out_dir, patterns_root=PATTERNS_ROOT,
        )
        text = out.read_text(encoding="utf-8")
        self.assertIn("has_hitl: true", text)
        self.assertIn("has_phases: true", text)


class TestPhaseDesignerCLI(unittest.TestCase):
    """CLI smoke test: build a phase-designer pack for the acme fixture via
    the script entrypoint and assert the generated input.md has the shape
    skill-phase-designer expects."""

    def test_cli_builds_phase_designer_pack(self):
        spec = ASSETS / "client-spec-examples" / "acme-board-memo.md"
        tmp = Path(tempfile.mkdtemp())
        cls_json = tmp / "cls.json"
        out_dir = tmp / "phases" / "02-skill-phase-designer"
        cls_json.write_text(json.dumps(tp.classify_spec(spec), indent=2), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS / "build_context_pack.py"),
                str(spec), str(cls_json), "skill-phase-designer", str(out_dir),
                "--patterns-root", str(PATTERNS_ROOT),
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        input_md = out_dir / "input.md"
        self.assertTrue(input_md.is_file())
        text = input_md.read_text(encoding="utf-8")
        # Phase-designer-specific structural expectations
        self.assertIn("# Input pack — skill-phase-designer", text)
        self.assertIn("## Procedure section", text)  # from the Task line
        self.assertIn("### Happy-path walkthrough", text)
        self.assertIn("bp-010-apply-once-carry-forward.md", text)


class TestStage7bAuditRegressions(unittest.TestCase):
    """Regression tests for the Stage 7b independent-review findings."""

    def test_render_traits_block_null_traits_coalesces(self):
        """SMELL #1: classifier with `"traits": null` must not crash.
        Repro before fix: AttributeError on `.get` of None."""
        out = bcp.render_traits_block({"traits": None}, [])
        # All 5 traits render as false when traits is null/missing
        for key in ["has_references", "has_phases", "has_hitl", "is_scheduled", "invokes_skills"]:
            self.assertIn(f"{key}: false", out)

    def test_render_traits_block_missing_traits_key(self):
        """Paired test: classifier missing the `traits` key entirely."""
        out = bcp.render_traits_block({}, [])
        for key in ["has_references", "has_phases", "has_hitl", "is_scheduled", "invokes_skills"]:
            self.assertIn(f"{key}: false", out)

    def test_resolve_bp_paths_rejects_unknown_subskill(self):
        """SMELL #2: resolve_bp_paths must raise ValueError (not KeyError) on
        unknown sub-skill, matching build_pack's validation for parity."""
        with self.assertRaises(ValueError) as cm:
            bcp.resolve_bp_paths("bogus", Path("/tmp"), firing_traits=None)
        # Error message lists the supported sub-skills for easy debugging
        self.assertIn("bogus", str(cm.exception))
        self.assertIn("skill-frontmatter", str(cm.exception))
        self.assertIn("skill-phase-designer", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
