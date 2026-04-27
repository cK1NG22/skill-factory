"""Unit tests for assemble_skill.py.

Run from skill-factory/:
    python3 -m unittest tests.test_assemble_skill -v
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

sys.path.insert(0, str(SCRIPTS))
import assemble_skill as asm  # noqa: E402


def _write_classifier(work: Path, **fires: bool) -> Path:
    """Write a minimal classifier.json with the named traits firing."""
    traits = {
        name: {"fires": bool(value), "evidence": "test"}
        for name, value in fires.items()
    }
    # Add un-named traits as not firing to keep parity with real output.
    for name in (
        "has_phases", "has_references", "has_hitl",
        "is_scheduled", "invokes_skills",
    ):
        traits.setdefault(name, {"fires": False, "evidence": "test"})
    path = work / "classifier.json"
    path.write_text(json.dumps({"traits": traits}), encoding="utf-8")
    return path


def _write_frontmatter_output(work: Path, slug: str = "fake-skill") -> None:
    phase = work / "phases" / "03-skill-frontmatter"
    phase.mkdir(parents=True, exist_ok=True)
    yaml_body = textwrap.dedent(f"""
        ---
        name: {slug}
        description: A fake skill for testing assembly. Use when "test
            assembly" or "fake skill". Do NOT use for real work.
        allowed-tools:
          - Read
        ---
    """).strip()
    (phase / "output.yaml").write_text(yaml_body, encoding="utf-8")
    # input.md carries the spec excerpt that the assembler may mine for body
    input_md = textwrap.dedent(f"""
        # Input pack — skill-frontmatter

        ## Spec excerpt

        ### Skill slug
        {slug}

        ### One-line description
        A fake skill for assembly testing.

        ### Happy-path walkthrough
        1. Load the input.
        2. Process the input.
        3. Write the output.
    """).strip()
    (phase / "input.md").write_text(input_md, encoding="utf-8")


def _write_phase_designer_output(work: Path) -> None:
    phase = work / "phases" / "04-skill-phase-designer"
    phase.mkdir(parents=True, exist_ok=True)
    body = textwrap.dedent("""
        ## Procedure

        ### Step 1 — Load input

        Read the input file.

        ### Step 2 — Process

        Run the transformation.

        ### Step 3 — Write output

        Write the result to disk.
    """).strip()
    (phase / "output.md").write_text(body, encoding="utf-8")


def _write_refs_target(work: Path, *names: str) -> None:
    target = (
        work / "phases" / "05-skill-references-scaffolder" / "target"
    )
    refs = target / "references"
    refs.mkdir(parents=True, exist_ok=True)
    for name in names:
        (refs / name).write_text(f"# {Path(name).stem}\n", encoding="utf-8")


def _write_cron_snippet(work: Path, fenced: bool = True) -> None:
    phase = work / "phases" / "06-skill-cron-observability"
    phase.mkdir(parents=True, exist_ok=True)
    if fenced:
        body = (
            "Snippet rationale.\n\n"
            "```python\n"
            "from pathlib import Path\n"
            "result = {'last_run': '2026-04-27', 'success': True}\n"
            "```\n"
        )
    else:
        body = "no python fence here, just narrative.\n"
    (phase / "instrumentation-snippet.md").write_text(body, encoding="utf-8")


def _write_signature_script(work: Path) -> None:
    phase = work / "phases" / "07-skill-signed-handoff"
    phase.mkdir(parents=True, exist_ok=True)
    (phase / "output-signature-template.py").write_text(
        "#!/usr/bin/env python3\nSIGNED_FIELDS = ['arg']\n",
        encoding="utf-8",
    )


# ---------- Always-fires happy path ----------


class TestAssembleNoTraits(unittest.TestCase):
    """Minimal factory run: only Phase 3 ran (frontmatter is always-fires).
    No optional phases. Assembled tree carries only SKILL.md + manifest."""

    def test_creates_skill_md_with_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work, slug="acme-thing")
            result = asm.assemble(work)
            self.assertTrue(result.assembled_dir.exists())
            self.assertEqual(result.assembled_dir.name, "acme-thing")
            skill_md = (result.assembled_dir / "SKILL.md").read_text()
            self.assertTrue(skill_md.startswith("---\n"))
            self.assertIn("name: acme-thing", skill_md)
            self.assertIn("# acme-thing", skill_md)

    def test_skill_md_includes_description_and_walkthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work)
            result = asm.assemble(work)
            skill_md = (result.assembled_dir / "SKILL.md").read_text()
            self.assertIn("A fake skill for assembly testing.", skill_md)
            self.assertIn("## Happy-path walkthrough", skill_md)
            self.assertIn("Load the input", skill_md)

    def test_no_procedure_when_has_phases_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work)
            result = asm.assemble(work)
            skill_md = (result.assembled_dir / "SKILL.md").read_text()
            self.assertNotIn("## Procedure", skill_md)

    def test_manifest_written_with_minimal_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work, slug="acme-thing")
            result = asm.assemble(work)
            manifest_path = result.assembled_dir / "ASSEMBLY-MANIFEST.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["slug"], "acme-thing")
            self.assertEqual(manifest["firing_traits"], [])
            self.assertEqual(manifest["skill_md"], "SKILL.md")
            self.assertIn("03-skill-frontmatter", manifest["from_phases"])


# ---------- has_phases gate ----------


class TestAssembleWithPhases(unittest.TestCase):
    """has_phases.fires → Phase 4 output appended; phases/ scaffolded."""

    def test_procedure_section_in_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True)
            _write_frontmatter_output(work)
            _write_phase_designer_output(work)
            result = asm.assemble(work)
            skill_md = (result.assembled_dir / "SKILL.md").read_text()
            self.assertIn("## Procedure", skill_md)
            self.assertIn("### Step 1 — Load input", skill_md)

    def test_phases_dir_scaffolded(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True)
            _write_frontmatter_output(work)
            _write_phase_designer_output(work)
            result = asm.assemble(work)
            self.assertTrue((result.assembled_dir / "phases").is_dir())

    def test_missing_phase_designer_output_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True)
            _write_frontmatter_output(work)
            # No Phase 4 output written → required, must raise
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn(
                "04-skill-phase-designer", str(cm.exception)
            )

    def test_empty_phase_designer_output_raises_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True)
            _write_frontmatter_output(work)
            phase = work / "phases" / "04-skill-phase-designer"
            phase.mkdir(parents=True, exist_ok=True)
            (phase / "output.md").write_text("", encoding="utf-8")
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 2)


# ---------- has_references gate ----------


class TestAssembleWithReferences(unittest.TestCase):
    def test_references_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_references=True)
            _write_frontmatter_output(work)
            _write_refs_target(work, "alpha.md", "beta.md")
            result = asm.assemble(work)
            refs = result.assembled_dir / "references"
            self.assertTrue(refs.is_dir())
            names = sorted(p.name for p in refs.iterdir())
            self.assertEqual(names, ["alpha.md", "beta.md"])

    def test_manifest_records_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_references=True)
            _write_frontmatter_output(work)
            _write_refs_target(work, "alpha.md")
            result = asm.assemble(work)
            self.assertEqual(result.manifest.get("references"), ["alpha.md"])

    def test_missing_refs_target_is_noop(self):
        """has_references fired but Phase 5 target dir doesn't exist —
        skip gracefully (the gate will catch it as a content-level fault)."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_references=True)
            _write_frontmatter_output(work)
            result = asm.assemble(work)
            # No references/ dir created
            self.assertFalse((result.assembled_dir / "references").exists())


# ---------- is_scheduled gate ----------


class TestAssembleWithCron(unittest.TestCase):
    def test_extracts_python_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, is_scheduled=True)
            _write_frontmatter_output(work)
            _write_cron_snippet(work, fenced=True)
            result = asm.assemble(work)
            snippet = (
                result.assembled_dir / "scripts"
                / "instrumentation_snippet.py"
            )
            self.assertTrue(snippet.exists())
            body = snippet.read_text(encoding="utf-8")
            self.assertIn("from pathlib import Path", body)
            self.assertIn("'last_run'", body)

    def test_falls_back_to_md_when_no_python_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, is_scheduled=True)
            _write_frontmatter_output(work)
            _write_cron_snippet(work, fenced=False)
            result = asm.assemble(work)
            scripts_dir = result.assembled_dir / "scripts"
            self.assertTrue(
                (scripts_dir / "instrumentation-snippet.md").exists()
            )

    def test_manifest_records_cron_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, is_scheduled=True)
            _write_frontmatter_output(work)
            _write_cron_snippet(work, fenced=True)
            result = asm.assemble(work)
            self.assertIn(
                "instrumentation_snippet.py",
                result.manifest.get("scripts", []),
            )


# ---------- AND gate (signed-handoff) ----------


class TestAssembleSignedHandoff(unittest.TestCase):
    def test_signature_script_copied_when_both_fire(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True, invokes_skills=True)
            _write_frontmatter_output(work, slug="my-pipeline")
            _write_phase_designer_output(work)
            _write_signature_script(work)
            result = asm.assemble(work)
            sig = (
                result.assembled_dir / "scripts"
                / "my-pipeline_signature.py"
            )
            self.assertTrue(sig.exists())
            self.assertIn("SIGNED_FIELDS", sig.read_text())

    def test_signature_skipped_when_only_phases_fires(self):
        """has_phases alone shouldn't pull in signed-handoff output."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True, invokes_skills=False)
            _write_frontmatter_output(work, slug="my-pipeline")
            _write_phase_designer_output(work)
            _write_signature_script(work)  # present but should be ignored
            result = asm.assemble(work)
            scripts_dir = result.assembled_dir / "scripts"
            if scripts_dir.exists():
                self.assertNotIn(
                    "my-pipeline_signature.py",
                    [p.name for p in scripts_dir.iterdir()],
                )

    def test_manifest_records_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work, has_phases=True, invokes_skills=True)
            _write_frontmatter_output(work, slug="my-pipeline")
            _write_phase_designer_output(work)
            _write_signature_script(work)
            result = asm.assemble(work)
            self.assertIn(
                "my-pipeline_signature.py",
                result.manifest.get("scripts", []),
            )


# ---------- Required-input failure modes ----------


class TestAssemblyErrors(unittest.TestCase):
    def test_missing_classifier_raises_code_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_frontmatter_output(work)
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 1)

    def test_malformed_classifier_raises_code_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "classifier.json").write_text("not json", encoding="utf-8")
            _write_frontmatter_output(work)
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 2)

    def test_missing_frontmatter_raises_code_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 1)

    def test_empty_frontmatter_yaml_raises_code_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            phase = work / "phases" / "03-skill-frontmatter"
            phase.mkdir(parents=True)
            (phase / "output.yaml").write_text("---\n---\n", encoding="utf-8")
            with self.assertRaises(asm.AssemblyError) as cm:
                asm.assemble(work)
            self.assertEqual(cm.exception.code, 2)

    def test_frontmatter_without_name_falls_back_to_input_md(self):
        """The frontmatter slug is canonical, but if it can't be parsed,
        the spec excerpt's `### Skill slug` block is the fallback."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            phase = work / "phases" / "03-skill-frontmatter"
            phase.mkdir(parents=True)
            # No `name:` in the YAML — assembler must use input.md fallback
            (phase / "output.yaml").write_text(
                "---\ndescription: foo\n---\n", encoding="utf-8"
            )
            (phase / "input.md").write_text(
                "## Spec excerpt\n\n### Skill slug\nfallback-slug\n",
                encoding="utf-8",
            )
            result = asm.assemble(work)
            self.assertEqual(result.assembled_dir.name, "fallback-slug")


# ---------- Idempotency ----------


class TestAssemblyIdempotency(unittest.TestCase):
    def test_rerun_overwrites_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work, slug="acme-thing")
            asm.assemble(work)
            stale = work / "assembled" / "acme-thing" / "stale-leftover.txt"
            stale.write_text("should be removed on re-run", encoding="utf-8")
            asm.assemble(work)
            self.assertFalse(stale.exists())


# ---------- CLI ----------


class TestAssembleCLI(unittest.TestCase):
    def test_cli_no_args_returns_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "assemble_skill.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_invalid_work_dir_returns_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "assemble_skill.py"),
             "/nonexistent-path-asdf-1234"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_success_prints_assembled_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            _write_frontmatter_output(work, slug="cli-test")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "assemble_skill.py"),
                 str(work)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("cli-test", result.stdout.strip())

    def test_cli_missing_required_phase_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            _write_classifier(work)
            # No frontmatter output → required, exit 1
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "assemble_skill.py"),
                 str(work)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
