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


class TestStage9aWiring(unittest.TestCase):
    """Stage 9a: registration + pack-shape + pre-scaffold for the two
    Wave-3 sub-skills wired into the driver (skill-references-scaffolder,
    skill-cron-observability)."""

    # ---------- Registration checks ----------

    def test_refs_scaffolder_registered_in_all_4_tier1_dicts(self):
        """Tier-1 cheat-sheet contract: every sub-skill must appear in all
        4 always-edit dicts. Skipping one silently breaks pack materialization."""
        for registry in (
            bcp._SUB_SKILL_BPS,
            bcp._SUB_SKILL_SECTIONS,
            bcp._SUB_SKILL_OUTPUT_BLURB,
            bcp._SUB_SKILL_TASK,
        ):
            self.assertIn("skill-references-scaffolder", registry)

    def test_cron_observability_registered_in_all_4_tier1_dicts(self):
        for registry in (
            bcp._SUB_SKILL_BPS,
            bcp._SUB_SKILL_SECTIONS,
            bcp._SUB_SKILL_OUTPUT_BLURB,
            bcp._SUB_SKILL_TASK,
        ):
            self.assertIn("skill-cron-observability", registry)

    # ---------- BP path resolution ----------

    def test_resolve_bp_paths_refs_scaffolder_base(self):
        """No traits → BP-007 + BP-008 only (BP-009 is conditional)."""
        paths = bcp.resolve_bp_paths(
            "skill-references-scaffolder", PATTERNS_ROOT, firing_traits=None
        )
        names = [Path(p).name for p in paths]
        self.assertEqual(
            names,
            [
                "bp-007-references-loaded-on-demand.md",
                "bp-008-references-one-level-deep.md",
            ],
        )

    def test_resolve_bp_paths_refs_scaffolder_with_has_phases(self):
        """has_phases trait → BP-009 unioned in (after the base BPs, in
        declaration order)."""
        paths = bcp.resolve_bp_paths(
            "skill-references-scaffolder", PATTERNS_ROOT, firing_traits=["has_phases"]
        )
        names = [Path(p).name for p in paths]
        self.assertEqual(
            names,
            [
                "bp-007-references-loaded-on-demand.md",
                "bp-008-references-one-level-deep.md",
                "bp-009-parallel-folders.md",
            ],
        )

    def test_resolve_bp_paths_cron_observability_unaffected_by_traits(self):
        """cron has no _SUB_SKILL_CONDITIONAL_BPS entry — same BPs regardless
        of which traits fire."""
        base = bcp.resolve_bp_paths(
            "skill-cron-observability", PATTERNS_ROOT, firing_traits=None
        )
        with_phases = bcp.resolve_bp_paths(
            "skill-cron-observability", PATTERNS_ROOT, firing_traits=["has_phases", "has_hitl"]
        )
        self.assertEqual(base, with_phases)
        names = [Path(p).name for p in base]
        # BP-022 + BP-021 always — BP-022 listed first (the contract-defining BP)
        self.assertEqual(
            names,
            [
                "bp-022-cron-observability.md",
                "bp-021-output-home.md",
            ],
        )

    # ---------- Reference-exemplars parser ----------

    def test_parse_reference_exemplars_extracts_filename_and_purpose(self):
        body = textwrap.dedent("""
            - `scoping-questions.md` — full intake checklist to ask the client.
            - `frameworks-map.md` — per-problem framework map.
            - `anti-patterns.md` — canonical failure-mode catalog.
        """).strip()
        refs = bcp.parse_reference_exemplars(body)
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0], ("scoping-questions.md", "full intake checklist to ask the client."))
        self.assertEqual(refs[2][0], "anti-patterns.md")

    def test_parse_reference_exemplars_handles_empty(self):
        self.assertEqual(bcp.parse_reference_exemplars(None), [])
        self.assertEqual(bcp.parse_reference_exemplars(""), [])
        self.assertEqual(bcp.parse_reference_exemplars("no bullets here"), [])

    # ---------- Pre-scaffold helper ----------

    def test_prescaffold_references_creates_placeholder_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                # Spec
                ## Company
                acme
                ## Skill slug
                test-skill
                ## Reference exemplars
                - `intake.md` — questions to ask first.
                - `frameworks.md` — strategy frameworks
                - `glossary.md` — domain terminology!
            """).strip(), encoding="utf-8")

            target = tmp / "scaffolded"
            refs = bcp.prescaffold_references(spec, target)

            self.assertEqual([n for n, _ in refs], ["intake.md", "frameworks.md", "glossary.md"])
            self.assertTrue((target / "references" / "intake.md").is_file())
            self.assertTrue((target / "references" / "frameworks.md").is_file())
            self.assertTrue((target / "references" / "glossary.md").is_file())
            self.assertTrue((target / "SKILL.md").is_file())

            skill_text = (target / "SKILL.md").read_text(encoding="utf-8")
            # Stub frontmatter + canonical citations. All three citation lines
            # must end in a SINGLE trailing period — neither doubled (when the
            # spec purpose already ended in `.`) nor missing (when it didn't).
            self.assertIn("name: scaffolded-skill-stub", skill_text)
            self.assertIn("Read `references/intake.md` for questions to ask first.", skill_text)
            self.assertNotIn("Read `references/intake.md` for questions to ask first..", skill_text)
            self.assertIn("Read `references/frameworks.md` for strategy frameworks.", skill_text)
            self.assertIn("Read `references/glossary.md` for domain terminology.", skill_text)

    def test_prescaffold_references_no_section_returns_empty(self):
        """Spec without a Reference exemplars section → no-op, returns []."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text("## Company\nacme\n", encoding="utf-8")
            refs = bcp.prescaffold_references(spec, tmp / "scaffolded")
            self.assertEqual(refs, [])
            # No directories created when there's nothing to scaffold
            self.assertFalse((tmp / "scaffolded" / "references").exists())

    def test_prescaffold_references_with_has_phases_creates_phases_dir(self):
        """Stage 9b regression — caught by omnibus 5-trait E2E. When
        has_phases AND has_references both fire, the pre-scaffold must
        create an empty phases/ alongside references/ so
        references_lint.py --has-phases doesn't fail BP-009 on a missing
        phases/ sibling. Without this, the omnibus E2E hit a first-attempt
        lint fail."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                ## Reference exemplars
                - `intake.md` — questions to ask first.
            """).strip(), encoding="utf-8")
            target = tmp / "scaffolded"

            # Without has_phases: only references/ created
            bcp.prescaffold_references(spec, target)
            self.assertTrue((target / "references").is_dir())
            self.assertFalse((target / "phases").exists())

            # With has_phases: phases/ also created
            target2 = tmp / "scaffolded2"
            bcp.prescaffold_references(spec, target2, has_phases=True)
            self.assertTrue((target2 / "references").is_dir())
            self.assertTrue((target2 / "phases").is_dir())

    # ---------- target_skill_dir block in pack ----------

    def test_target_skill_dir_block_appears_when_provided(self):
        """When build_pack receives target_skill_dir, the materialized
        input.md gets a `## Target skill directory` block between BPs and
        Output locations."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                # Spec
                ## Company
                acme
                ## Skill slug
                test
                ## One-line description
                Does X.
                ## Trigger phrases
                - run X
                ## Inputs
                None.
                ## Outputs
                A thing.
                ## Happy-path walkthrough
                1. Read input.
                ## Reference exemplars
                - `notes.md` — a note.
            """).strip(), encoding="utf-8")
            classifier = tmp / "classifier.json"
            classifier.write_text(json.dumps({
                "traits": {
                    "has_references": {"fires": True},
                    "has_phases": {"fires": False},
                    "has_hitl": {"fires": False},
                    "is_scheduled": {"fires": False},
                    "invokes_skills": {"fires": False},
                }
            }), encoding="utf-8")
            out_dir = tmp / "phase05"
            target = tmp / "scaffolded"

            input_md = bcp.build_pack(
                spec_path=spec,
                classifier_path=classifier,
                sub_skill_name="skill-references-scaffolder",
                out_dir=out_dir,
                patterns_root=PATTERNS_ROOT,
                target_skill_dir=target,
            )
            text = input_md.read_text(encoding="utf-8")
            self.assertIn("## Target skill directory", text)
            self.assertIn(str(target), text)
            # Block ordering: appears between BPs and Output locations
            bps_pos = text.index("## BPs to enforce")
            target_pos = text.index("## Target skill directory")
            output_pos = text.index("## Output locations")
            self.assertTrue(bps_pos < target_pos < output_pos)

    def test_target_skill_dir_block_omitted_by_default(self):
        """When build_pack is called without target_skill_dir, no
        `## Target skill directory` block appears (preserves backward compat
        for skill-frontmatter / skill-phase-designer wiring)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                # Spec
                ## Company
                acme
                ## Skill slug
                t
                ## One-line description
                X.
                ## Trigger phrases
                - run
                ## Inputs
                None.
                ## Outputs
                A.
                ## Happy-path walkthrough
                1. Step.
                ## Anti-goals
                None.
            """).strip(), encoding="utf-8")
            classifier = tmp / "classifier.json"
            classifier.write_text(json.dumps({"traits": {}}), encoding="utf-8")
            out_dir = tmp / "phase03"

            input_md = bcp.build_pack(
                spec_path=spec,
                classifier_path=classifier,
                sub_skill_name="skill-frontmatter",
                out_dir=out_dir,
                patterns_root=PATTERNS_ROOT,
            )
            text = input_md.read_text(encoding="utf-8")
            self.assertNotIn("## Target skill directory", text)

    # ---------- CLI integration ----------

    def test_cli_prescaffold_references_mode(self):
        """`build_context_pack.py --prescaffold-references <spec> <target>`
        creates the placeholder tree and prints {"scaffolded": [...]} JSON."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                ## Reference exemplars
                - `a.md` — first.
                - `b.md` — second.
            """).strip(), encoding="utf-8")
            target = tmp / "target"

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_context_pack.py"),
                 "--prescaffold-references", str(spec), str(target)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout.strip())
            # Stage 9b enriched the payload with has_phases — assert the
            # scaffolded list specifically, not the whole dict shape, so this
            # test stays forward-compatible if more fields are added.
            self.assertEqual(payload["scaffolded"], ["a.md", "b.md"])
            # Without --has-phases flag, has_phases defaults to False
            self.assertFalse(payload.get("has_phases", False))
            self.assertTrue((target / "references" / "a.md").is_file())
            self.assertTrue((target / "references" / "b.md").is_file())
            self.assertTrue((target / "SKILL.md").is_file())
            # Without --has-phases, no phases/ dir created
            self.assertFalse((target / "phases").exists())


class TestStage9bWiring(unittest.TestCase):
    """Stage 9b: predicate registry + signed-handoff wiring + AND-intersection
    trigger. The first compound trigger in the factory."""

    # ---------- Predicate registry ----------

    def test_signed_handoff_registered_in_all_4_tier1_dicts(self):
        for registry in (
            bcp._SUB_SKILL_BPS,
            bcp._SUB_SKILL_SECTIONS,
            bcp._SUB_SKILL_OUTPUT_BLURB,
            bcp._SUB_SKILL_TASK,
        ):
            self.assertIn("skill-signed-handoff", registry)

    def test_signed_handoff_registered_in_predicate_registry(self):
        """Tier 3 — the AND-intersection sub-skill MUST be in the predicate
        registry (otherwise should_fire's default-to-True would let it fire
        on every spec, including non-pipeline ones)."""
        self.assertIn("skill-signed-handoff", bcp._SUB_SKILL_TRIGGER_PREDICATE)

    def test_signed_handoff_predicate_AND_semantics(self):
        """The predicate must implement boolean AND of has_phases + invokes_skills."""
        predicate = bcp._SUB_SKILL_TRIGGER_PREDICATE["skill-signed-handoff"]
        # Both true → fire
        self.assertTrue(predicate({
            "has_phases": {"fires": True}, "invokes_skills": {"fires": True}
        }))
        # Either false → skip
        self.assertFalse(predicate({
            "has_phases": {"fires": True}, "invokes_skills": {"fires": False}
        }))
        self.assertFalse(predicate({
            "has_phases": {"fires": False}, "invokes_skills": {"fires": True}
        }))
        # Neither set → skip (defensive against missing keys)
        self.assertFalse(predicate({}))

    def test_should_fire_default_to_true_for_unregistered(self):
        """Sub-skills NOT in the predicate registry default to True — driver
        SKILL.md does the gating via inline trait reads (Pattern A)."""
        # frontmatter is always-fires; not in predicate registry
        self.assertTrue(bcp.should_fire("skill-frontmatter", {"traits": {}}))
        # phase-designer is single-trait; not in predicate registry
        self.assertTrue(bcp.should_fire("skill-phase-designer", {"traits": {}}))
        # refs-scaffolder is single-trait; not in predicate registry
        self.assertTrue(bcp.should_fire("skill-references-scaffolder", {"traits": {}}))
        # cron is single-trait; not in predicate registry
        self.assertTrue(bcp.should_fire("skill-cron-observability", {"traits": {}}))

    def test_should_fire_signed_handoff_AND_gate(self):
        """should_fire on signed-handoff uses the AND predicate."""
        both_fire = {"traits": {
            "has_phases": {"fires": True}, "invokes_skills": {"fires": True}
        }}
        only_phases = {"traits": {
            "has_phases": {"fires": True}, "invokes_skills": {"fires": False}
        }}
        self.assertTrue(bcp.should_fire("skill-signed-handoff", both_fire))
        self.assertFalse(bcp.should_fire("skill-signed-handoff", only_phases))

    def test_should_fire_rejects_unknown_subskill(self):
        """Parity with build_pack / resolve_bp_paths: unknown sub-skill →
        ValueError, not KeyError."""
        with self.assertRaises(ValueError) as cm:
            bcp.should_fire("bogus", {"traits": {}})
        self.assertIn("bogus", str(cm.exception))
        self.assertIn("skill-signed-handoff", str(cm.exception))

    def test_should_fire_handles_null_traits(self):
        """Stage 7b regression class: classifier with `traits: null` must
        not crash should_fire (parity with render_traits_block fix)."""
        # default-to-True path
        self.assertTrue(bcp.should_fire("skill-frontmatter", {"traits": None}))
        # predicate-registered path — predicate handles missing traits via .get
        self.assertFalse(bcp.should_fire("skill-signed-handoff", {"traits": None}))

    # ---------- BP resolution ----------

    def test_resolve_bp_paths_signed_handoff_base(self):
        """Only BP-024 ships in the pack — meta BPs (BP-028, BP-033) are
        factory-internal discipline self-applied by the sub-skill."""
        paths = bcp.resolve_bp_paths(
            "skill-signed-handoff", PATTERNS_ROOT, firing_traits=None
        )
        names = [Path(p).name for p in paths]
        self.assertEqual(names, ["bp-024-signed-handoffs.md"])

    def test_resolve_bp_paths_signed_handoff_unaffected_by_traits(self):
        """signed-handoff has no _SUB_SKILL_CONDITIONAL_BPS entry — same BPs
        regardless of which other traits fire (the AND-trigger is the entire
        gate; further conditionals would be redundant)."""
        base = bcp.resolve_bp_paths("skill-signed-handoff", PATTERNS_ROOT)
        with_all = bcp.resolve_bp_paths(
            "skill-signed-handoff", PATTERNS_ROOT,
            firing_traits=["has_phases", "invokes_skills", "has_hitl",
                           "is_scheduled", "has_references"]
        )
        self.assertEqual(base, with_all)

    # ---------- Pack shape ----------

    def test_signed_handoff_pack_shape(self):
        """The materialized input.md for signed-handoff carries the standard
        section ordering plus optional Pipeline composition / Argument-bearing
        fields when the spec declares them."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                # Spec
                ## Company
                acme
                ## Skill slug
                pipeline-deck
                ## One-line description
                Deck builder downstream of /acme-case.
                ## Trigger phrases
                - build pipeline deck
                ## Inputs
                Spec from upstream.
                ## Outputs
                A deck.
                ## Happy-path walkthrough
                1. Verify signature.
                2. Build deck.
                3. Sign output.
                ## Success signals
                Deck builds.
                ## Failure modes
                Sig mismatch → exit 1.
                ## Existing skills to reuse
                - `/acme-case` — upstream producer.
                ## Pipeline composition
                Upstream `/acme-case` writes spec; this skill verifies + consumes.
                ## Argument-bearing fields
                - `argument_flow`
                - `recommendation`
            """).strip(), encoding="utf-8")
            classifier = tmp / "classifier.json"
            classifier.write_text(json.dumps({
                "traits": {
                    "has_phases": {"fires": True},
                    "invokes_skills": {"fires": True},
                    "has_references": {"fires": False},
                    "has_hitl": {"fires": False},
                    "is_scheduled": {"fires": False},
                }
            }), encoding="utf-8")

            input_md = bcp.build_pack(
                spec_path=spec, classifier_path=classifier,
                sub_skill_name="skill-signed-handoff",
                out_dir=tmp / "phase07",
                patterns_root=PATTERNS_ROOT,
            )
            text = input_md.read_text(encoding="utf-8")
            # Required structural elements
            self.assertIn("# Input pack — skill-signed-handoff", text)
            self.assertIn("Stamp a `<slug>_signature.py` script", text)
            self.assertIn("### Existing skills to reuse", text)
            self.assertIn("### Pipeline composition", text)
            self.assertIn("### Argument-bearing fields", text)
            self.assertIn("argument_flow", text)
            self.assertIn("bp-024-signed-handoffs.md", text)
            # Trait block: invokes_skills nests the slug
            self.assertIn("invokes_skills: true", text)
            self.assertIn("- /acme-case", text)
            # No Target skill directory block (signed-handoff doesn't need it)
            self.assertNotIn("## Target skill directory", text)

    # ---------- CLI integration ----------

    def test_cli_should_fire_returns_exit_0_when_predicate_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            classifier = Path(tmp) / "c.json"
            classifier.write_text(json.dumps({
                "traits": {
                    "has_phases": {"fires": True},
                    "invokes_skills": {"fires": True},
                }
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_context_pack.py"),
                 "--should-fire", "skill-signed-handoff", str(classifier)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload, {"sub_skill": "skill-signed-handoff", "fires": True})

    def test_cli_prescaffold_with_has_phases_flag(self):
        """Stage 9b regression: --has-phases flag must propagate to
        prescaffold_references and produce an empty phases/ dir."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text(textwrap.dedent("""
                ## Reference exemplars
                - `x.md` — first ref.
            """).strip(), encoding="utf-8")
            target = tmp / "target"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_context_pack.py"),
                 "--prescaffold-references", str(spec), str(target), "--has-phases"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload["scaffolded"], ["x.md"])
            self.assertTrue(payload["has_phases"])
            self.assertTrue((target / "phases").is_dir())

    def test_cli_should_fire_returns_exit_1_when_predicate_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            classifier = Path(tmp) / "c.json"
            classifier.write_text(json.dumps({
                "traits": {
                    "has_phases": {"fires": True},
                    "invokes_skills": {"fires": False},
                }
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_context_pack.py"),
                 "--should-fire", "skill-signed-handoff", str(classifier)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload, {"sub_skill": "skill-signed-handoff", "fires": False})


class TestStage10bWiring(unittest.TestCase):
    """Stage 10b: skill-compliance-gate registration + minimal-pack schema.

    The gate is the first sub-skill in the factory whose input.md schema
    deviates from the standard spec-driven shape. It carries only
    `assembled_skill_path` + `work_dir` (per plan D1). The standard
    Tier-1/2/3 dicts still need symmetric entries so every other piece
    of the pipeline (resolve_bp_paths, should_fire, error messages)
    treats the gate as a first-class sub-skill.
    """

    # ---------- Tier-1 / Tier-2 / Tier-3 registration ----------

    def test_gate_registered_in_all_4_tier1_dicts(self):
        for registry in (
            bcp._SUB_SKILL_BPS,
            bcp._SUB_SKILL_SECTIONS,
            bcp._SUB_SKILL_OUTPUT_BLURB,
            bcp._SUB_SKILL_TASK,
        ):
            self.assertIn("skill-compliance-gate", registry)

    def test_gate_has_no_tier2_conditional_entries(self):
        """The gate's behavior is fixed — it audits everything, every run."""
        self.assertNotIn(
            "skill-compliance-gate", bcp._SUB_SKILL_CONDITIONAL_BPS
        )
        self.assertNotIn(
            "skill-compliance-gate", bcp._SUB_SKILL_CONDITIONAL_SECTIONS
        )

    def test_gate_not_in_predicate_registry(self):
        """Gate is universal-fires; should_fire's default-to-True applies."""
        self.assertNotIn(
            "skill-compliance-gate", bcp._SUB_SKILL_TRIGGER_PREDICATE
        )

    def test_should_fire_gate_always_true(self):
        # Empty / null / missing / present-with-nothing-firing — all fire.
        self.assertTrue(bcp.should_fire("skill-compliance-gate", {"traits": {}}))
        self.assertTrue(
            bcp.should_fire("skill-compliance-gate", {"traits": None})
        )
        self.assertTrue(bcp.should_fire("skill-compliance-gate", {}))
        self.assertTrue(bcp.should_fire("skill-compliance-gate", {
            "traits": {"has_phases": {"fires": False}}
        }))

    # ---------- BP list ----------

    def test_resolve_bp_paths_gate_empty(self):
        """Empty BP list — gate's checks are hardcoded in compliance_check.py
        (Family 1) and gate.py (Family 2 / Check 14)."""
        paths = bcp.resolve_bp_paths(
            "skill-compliance-gate", PATTERNS_ROOT, firing_traits=None
        )
        self.assertEqual(paths, [])

    def test_resolve_bp_paths_gate_empty_regardless_of_traits(self):
        with_all = bcp.resolve_bp_paths(
            "skill-compliance-gate", PATTERNS_ROOT,
            firing_traits=["has_phases", "invokes_skills", "has_hitl",
                           "is_scheduled", "has_references"],
        )
        self.assertEqual(with_all, [])

    # ---------- Pack shape (minimal schema) ----------

    def test_build_pack_gate_requires_assembled_skill_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with self.assertRaises(ValueError) as cm:
                bcp.build_pack(
                    spec_path=tmp / "spec.md",  # unused by gate
                    classifier_path=tmp / "c.json",  # unused by gate
                    sub_skill_name="skill-compliance-gate",
                    out_dir=tmp / "phase08",
                    patterns_root=PATTERNS_ROOT,
                    work_dir=tmp,  # provided
                    # assembled_skill_path missing → ValueError
                )
            self.assertIn("assembled_skill_path", str(cm.exception))

    def test_build_pack_gate_requires_work_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with self.assertRaises(ValueError) as cm:
                bcp.build_pack(
                    spec_path=tmp / "spec.md",
                    classifier_path=tmp / "c.json",
                    sub_skill_name="skill-compliance-gate",
                    out_dir=tmp / "phase08",
                    patterns_root=PATTERNS_ROOT,
                    assembled_skill_path=tmp / "assembled",
                )
            self.assertIn("work_dir", str(cm.exception))

    def test_build_gate_pack_writes_minimal_input_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assembled = tmp / "assembled" / "fake-skill"
            assembled.mkdir(parents=True)
            input_md = bcp.build_gate_pack(
                out_dir=tmp / "phase08",
                assembled_skill_path=assembled,
                work_dir=tmp,
            )
            self.assertTrue(input_md.exists())
            text = input_md.read_text(encoding="utf-8")
            self.assertIn("# Input pack — skill-compliance-gate", text)
            # Gate's parser expects `- **key**: value` lines
            self.assertIn(f"- **assembled_skill_path**: {assembled}", text)
            self.assertIn(f"- **work_dir**: {tmp}", text)

    def test_gate_pack_skips_standard_sections(self):
        """Minimal schema — no Spec excerpt, no Classified traits, no BPs."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            input_md = bcp.build_gate_pack(
                out_dir=tmp / "phase08",
                assembled_skill_path=tmp / "fake",
                work_dir=tmp,
            )
            text = input_md.read_text(encoding="utf-8")
            self.assertNotIn("## Spec excerpt", text)
            self.assertNotIn("## Classified traits", text)
            self.assertNotIn("## BPs to enforce", text)
            # But the standard structural sections are present
            self.assertIn("## Task", text)
            self.assertIn("## Output locations", text)

    def test_gate_pack_parseable_by_gate_input_parser(self):
        """End-to-end: skill-compliance-gate's parse_input_md must extract
        the two fields the pack emits, exactly as gate.py reads them."""
        gate_scripts = (
            REPO_SKILL.parent / "skill-compliance-gate" / "scripts"
        )
        sys.path.insert(0, str(gate_scripts))
        try:
            import gate as gate_module  # noqa: WPS433
        finally:
            # Don't leave it on sys.path for other tests.
            if str(gate_scripts) in sys.path:
                sys.path.remove(str(gate_scripts))

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assembled = tmp / "assembled" / "fake-skill"
            input_md = bcp.build_gate_pack(
                out_dir=tmp / "phase08",
                assembled_skill_path=assembled,
                work_dir=tmp,
            )
            fields = gate_module.parse_input_md(input_md)
            self.assertEqual(
                fields.get("assembled_skill_path"), str(assembled)
            )
            self.assertEqual(fields.get("work_dir"), str(tmp))

    # ---------- CLI integration ----------

    def test_cli_gate_target_writes_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assembled = tmp / "assembled" / "fake-skill"
            assembled.mkdir(parents=True)
            spec = tmp / "spec.md"
            spec.write_text("# unused", encoding="utf-8")
            classifier = tmp / "c.json"
            classifier.write_text("{}", encoding="utf-8")
            out = tmp / "phase08"

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / "build_context_pack.py"),
                    str(spec), str(classifier), "skill-compliance-gate",
                    str(out),
                    "--assembled-skill-path", str(assembled),
                    "--work-dir", str(tmp),
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out / "input.md").exists())

    def test_cli_gate_target_rejects_missing_assembled_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            spec = tmp / "spec.md"
            spec.write_text("# unused", encoding="utf-8")
            classifier = tmp / "c.json"
            classifier.write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / "build_context_pack.py"),
                    str(spec), str(classifier), "skill-compliance-gate",
                    str(tmp / "phase08"),
                    "--work-dir", str(tmp),
                    # --assembled-skill-path missing
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("assembled_skill_path", result.stderr)


class TestStage11bPhase9Integration(unittest.TestCase):
    """Stage 11b — Phase 9 director + driver SKILL.md wiring.

    `materialize_skill.py` is an inline factory script (plan v2 D1), not
    a sub-skill, so it does NOT register in the build_context_pack.py
    Tier-1 dicts. These tests verify the source-tree shape grew the new
    phase dir + driver Procedure step cleanly:

      - Phase dir + 2 reference files exist at expected paths.
      - Driver SKILL.md has exactly 10 sequential Procedure steps.
      - Step 9 wires through to phases/09-materialize/director.md.
      - Step 10 (renumbered from old Step 9) wires through to phases/99-report/.
      - The new phase director phase-lints clean (catches imperative-opener
        and step-numbering regressions before they reach Phase 8's gate).
    """

    DRIVER_SKILL_MD = REPO_SKILL / "SKILL.md"
    PHASE_9_DIR = REPO_SKILL / "phases" / "09-materialize"

    def test_phase_9_director_file_exists(self):
        self.assertTrue(
            (self.PHASE_9_DIR / "director.md").is_file(),
            "Phase 9 director must exist at phases/09-materialize/director.md",
        )

    def test_phase_9_has_both_phase_scoped_references(self):
        refs = self.PHASE_9_DIR / "references"
        self.assertTrue((refs / "materialization-contract.md").is_file(),
                        "materialization-contract.md must exist (cited by "
                        "director Steps A/C/D)")
        self.assertTrue((refs / "gh-cli-invocation.md").is_file(),
                        "gh-cli-invocation.md must exist (cited by "
                        "director Step B)")

    def test_driver_skill_md_has_ten_sequential_steps(self):
        text = self.DRIVER_SKILL_MD.read_text(encoding="utf-8")
        # Count "### Step N — " headings inside the Procedure section.
        # Stage 11b grew the Procedure 9 → 10 steps per plan v2 D8.
        import re
        steps = re.findall(r"^###\s+Step\s+(\d+)\s+—", text, re.MULTILINE)
        self.assertEqual(
            [int(s) for s in steps], list(range(1, 11)),
            "Driver SKILL.md must have exactly 10 sequential Procedure "
            f"steps (Step 1 through Step 10); got: {steps}",
        )

    def test_driver_step_9_references_phase_9_director(self):
        text = self.DRIVER_SKILL_MD.read_text(encoding="utf-8")
        # Step 9 is the new materialize step. Must point at the phase 9
        # director path so the driver's runtime read happens correctly.
        import re
        m = re.search(r"### Step 9 .*?(?=### Step 10|## )", text,
                      re.DOTALL)
        self.assertIsNotNone(m, "Driver SKILL.md is missing Step 9")
        self.assertIn("phases/09-materialize/director.md", m.group(0),
                      "Step 9 must direct the runtime to read "
                      "phases/09-materialize/director.md")

    def test_references_lint_strict_walks_ten_phase_directors(self):
        """references_lint --strict-two-level must recognize the new
        Phase 9 director when walking the driver tree. The plan-specified
        canary for Stage 11b: if the lint walker doesn't see the 10th
        director, the strict citation check would silently skip it and
        let cross-phase reference rot land unnoticed."""
        ref_lint = (REPO_SKILL.parent / "skill-references-scaffolder"
                    / "scripts" / "references_lint.py")
        if not ref_lint.is_file():
            self.skipTest("references_lint.py not present in this checkout")
        result = subprocess.run(
            [sys.executable, str(ref_lint),
             str(REPO_SKILL), "--strict-two-level"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"references_lint failed on driver tree:\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}",
        )
        # Walk should report exactly 10 phase directors (was 9 before
        # Stage 11b). Look for the info line; format set in
        # skill-references-scaffolder Stage 9.0.
        self.assertIn(
            "10 phase director(s) inspected", result.stdout,
            f"Expected '10 phase director(s) inspected' in lint stdout, "
            f"got: {result.stdout}",
        )


if __name__ == "__main__":
    unittest.main()
