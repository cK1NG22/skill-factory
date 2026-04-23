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


if __name__ == "__main__":
    unittest.main()
