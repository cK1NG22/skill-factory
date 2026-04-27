"""Phase 8 end-to-end integration: assemble_skill.py → build_gate_pack →
gate.py against a synthetic work directory.

This is a lighter-weight version of the plan's `test_phase8_director.py`.
It does NOT spawn an actual Agent (that's the Stage 10c live E2E job) —
instead it drives each script directly via subprocess to verify the wire
contract: every script's output is consumable by the next.

Run from skill-factory/:
    python3 -m unittest tests.test_phase8_integration -v
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
GATE_SCRIPT = REPO_SKILL.parent / "skill-compliance-gate" / "scripts" / "gate.py"

sys.path.insert(0, str(SCRIPTS))
import assemble_skill as asm  # noqa: E402
import build_context_pack as bcp  # noqa: E402


def _setup_minimal_work(tmp: Path, slug: str = "synth-skill") -> Path:
    """Build a synthetic <work> dir that's just enough for the assembler:
    classifier.json + Phase 3 frontmatter output + Phase 4 procedure.

    The assembled tree from this fixture should pass the gate cleanly
    (no required-tier fails, no Check 14 hits)."""
    work = tmp / "work"
    work.mkdir()

    classifier = {"traits": {
        "has_phases": {"fires": True, "evidence": "test"},
        "has_references": {"fires": False, "evidence": "test"},
        "has_hitl": {"fires": False, "evidence": "test"},
        "is_scheduled": {"fires": False, "evidence": "test"},
        "invokes_skills": {"fires": False, "evidence": "test"},
    }}
    (work / "classifier.json").write_text(
        json.dumps(classifier), encoding="utf-8"
    )

    phase3 = work / "phases" / "03-skill-frontmatter"
    phase3.mkdir(parents=True)
    yaml_body = textwrap.dedent(f"""
        ---
        name: {slug}
        description: An end-to-end Phase 8 integration test fixture.
            Use when "test phase 8 integration" or "synth skill". Do NOT
            use for production work.
        argument-hint: "<input>"
        allowed-tools:
          - Read
          - Bash
        ---
    """).strip()
    (phase3 / "output.yaml").write_text(yaml_body, encoding="utf-8")
    (phase3 / "input.md").write_text(textwrap.dedent(f"""
        # Input pack — skill-frontmatter

        ## Spec excerpt

        ### Skill slug
        {slug}

        ### One-line description
        An end-to-end Phase 8 integration test fixture.

        ### Happy-path walkthrough
        1. Read the input.
        2. Run the transformation.
        3. Write the output.
    """).strip(), encoding="utf-8")

    phase4 = work / "phases" / "04-skill-phase-designer"
    phase4.mkdir(parents=True)
    (phase4 / "output.md").write_text(textwrap.dedent("""
        ## Procedure

        ### Step 1 — Read the input

        Read the input file from the path argument. Fail loudly on missing.

        ### Step 2 — Run the transformation

        Apply the deterministic transform to the input contents.

        ### Step 3 — Write the output

        Write the result to the output path. STOP.
    """).strip(), encoding="utf-8")

    return work


class TestPhase8Integration(unittest.TestCase):
    """The Phase 8 director's three scripts, chained.

    Step A (assemble_skill.py) → Step B (build_gate_pack via build_pack) →
    Step C (gate.py --input). The director (Step D) reads the gate's
    written verdict file. We verify that file exists and is well-formed.
    """

    def test_assembler_pack_gate_chain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            work = _setup_minimal_work(tmp)

            # --- Step A: assemble_skill.py ---
            result = asm.assemble(work)
            assembled = result.assembled_dir
            self.assertTrue((assembled / "SKILL.md").exists())
            self.assertTrue((assembled / "ASSEMBLY-MANIFEST.json").exists())

            # --- Step B: build_gate_pack ---
            phase8 = work / "phases" / "08-assemble-and-gate"
            input_md = bcp.build_gate_pack(
                out_dir=phase8,
                assembled_skill_path=assembled,
                work_dir=work,
            )
            self.assertTrue(input_md.exists())

            # --- Step C: gate.py --input ---
            res = subprocess.run(
                [sys.executable, str(GATE_SCRIPT), "--input", str(input_md)],
                capture_output=True, text=True, check=False,
            )
            # Gate wrote a verdict file — check which one.
            output_md = phase8 / "output.md"
            notes_md = phase8 / "notes.md"

            # On a clean PASS, gate writes output.md (no notes.md / no BLOCKER).
            # Gate.py exit code in --input mode mirrors the verdict (0/1).
            self.assertEqual(
                res.returncode, 0,
                f"gate failed; stdout={res.stdout}; stderr={res.stderr}; "
                f"notes={notes_md.read_text() if notes_md.exists() else '<absent>'}"
            )
            self.assertTrue(output_md.exists())
            output_text = output_md.read_text(encoding="utf-8")
            self.assertIn("PASS", output_text.upper())

            # Sanity: no BLOCKER line
            if notes_md.exists():
                notes_text = notes_md.read_text(encoding="utf-8")
                self.assertNotIn("BLOCKER:", notes_text)

    def test_gate_blocker_when_assembled_skill_has_meta_cite(self):
        """Inject a Check-14 violation into the assembled tree and confirm
        the gate writes a BLOCKER line. Validates the FAIL path of Step D."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            work = _setup_minimal_work(tmp)
            result = asm.assemble(work)
            assembled = result.assembled_dir

            # Create a references/ dir with a bad meta-BP citation.
            refs = assembled / "references"
            refs.mkdir(exist_ok=True)
            (refs / "tainted.md").write_text(
                "# Tainted reference\n\nSee bp-028 for the BLOCKER convention.\n",
                encoding="utf-8",
            )

            phase8 = work / "phases" / "08-assemble-and-gate"
            input_md = bcp.build_gate_pack(
                out_dir=phase8,
                assembled_skill_path=assembled,
                work_dir=work,
            )

            res = subprocess.run(
                [sys.executable, str(GATE_SCRIPT), "--input", str(input_md)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(res.returncode, 1)
            notes_md = phase8 / "notes.md"
            self.assertTrue(notes_md.exists())
            notes_text = notes_md.read_text(encoding="utf-8")
            self.assertIn("BLOCKER:", notes_text)
            self.assertIn("Check 14", notes_text)


if __name__ == "__main__":
    unittest.main()
