"""Unit tests for phase_lint.py — exercises each of the 6 rules.

Run from skill-phase-designer/:
    python3 -m unittest tests.test_phase_lint -v
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
import phase_lint as pl  # noqa: E402


GOOD_NO_HITL = textwrap.dedent("""
    ## Procedure

    ### Step 1 — Load the input
    Read the input `.md` file from the path argument. Fail fast with exit code 1 if the path does not exist.

    ### Step 2 — Validate required sections
    Validate that the four required top-level sections are present. Fail fast with a specific error naming the missing section if any is absent.

    ### Step 3 — Invoke /docx
    Invoke the `/docx` skill to construct the document. Populate the cover page with the title and metadata.

    ### Step 4 — Write output
    Write the finished `.docx` to `~/Claude/acme-board-memo/<input-stem>.docx`. Ensure the output directory exists.

    ### Step 5 — Print path
    Print the absolute output path to stdout.
""").strip()


GOOD_WITH_HITL = textwrap.dedent("""
    ## Procedure

    ### Step 1 — Read agenda
    Read the agenda YAML from the path argument. Announce that Phase 1 has begun.

    ### Step 2 — Confirm each topic
    Ask the user to confirm each topic. Number the confirmations:
    1. Is topic A on the agenda?
    2. Is topic B on the agenda?

    Do NOT proceed to Step 3 until all topics are confirmed.

    ### Step 3 — Gather talking points
    Prompt the user for talking points per topic. Wait for the user before moving on.

    ### Step 4 — Fetch financials
    Fetch prior-period financials from the reference lookup table.

    ### Step 5 — Assemble packet
    Assemble the packet using `/docx`.

    ### Step 6 — Confirm and write
    Present a preview. Invoke AskUserQuestion with options: ["approve", "revise"]. Do NOT proceed until approve is returned.
""").strip()


# ---------- Rule 1: Numbered and sequential ----------


class TestRule1Numbering(unittest.TestCase):
    def test_sequential_passes(self):
        result = pl.lint(GOOD_NO_HITL)
        seq_fails = [f for f in result.fails if "sequential" in f or "expected" in f]
        self.assertEqual(seq_fails, [], f"fails={result.fails}")

    def test_missing_steps_fails(self):
        text = "## Procedure\n\nJust a paragraph. No steps.\n"
        result = pl.lint(text)
        self.assertFalse(result.passed)
        self.assertTrue(any("no '### Step" in f for f in result.fails))

    def test_out_of_order_fails(self):
        text = textwrap.dedent("""
            ### Step 2 — Out of order
            Read the file.

            ### Step 1 — Second
            Write the file.
        """).strip()
        result = pl.lint(text)
        self.assertFalse(result.passed)
        self.assertTrue(any("sequential" in f or "expected" in f for f in result.fails))

    def test_gap_in_numbering_fails(self):
        text = textwrap.dedent("""
            ### Step 1 — First
            Read.

            ### Step 3 — Skip
            Write.
        """).strip()
        result = pl.lint(text)
        self.assertFalse(result.passed)


# ---------- Rule 2: Imperative verb ----------


class TestRule2ImperativeVerb(unittest.TestCase):
    def test_imperative_verbs_pass(self):
        result = pl.lint(GOOD_NO_HITL)
        verb_fails = [f for f in result.fails if "imperative-verb list" in f]
        self.assertEqual(verb_fails, [], result.fails)

    def test_non_imperative_fails(self):
        text = textwrap.dedent("""
            ### Step 1 — Start
            The file is read from disk.

            ### Step 2 — Finish
            Write the output.
        """).strip()
        result = pl.lint(text)
        # "the" is not imperative
        self.assertTrue(any("imperative-verb list" in f for f in result.fails), result.fails)

    def test_control_keyword_accepted(self):
        text = textwrap.dedent("""
            ### Step 1 — Loop
            For each item in the list: read the content.

            ### Step 2 — Branch
            If the input is missing: exit with code 1.

            ### Step 3 — Done
            Write the output.
        """).strip()
        result = pl.lint(text)
        verb_fails = [f for f in result.fails if "imperative-verb list" in f]
        self.assertEqual(verb_fails, [], result.fails)


# ---------- Rule 3: Weak voice ----------


class TestRule3WeakVoice(unittest.TestCase):
    def test_weak_voice_fails(self):
        text = textwrap.dedent("""
            ### Step 1 — Read
            Read the file. We should also validate the content.

            ### Step 2 — Write
            Write the output. You should verify the path.
        """).strip()
        result = pl.lint(text)
        self.assertTrue(any("weak/passive" in f for f in result.fails), result.fails)

    def test_no_weak_voice_passes(self):
        result = pl.lint(GOOD_NO_HITL)
        weak_fails = [f for f in result.fails if "weak/passive" in f]
        self.assertEqual(weak_fails, [], result.fails)


# ---------- Rule 4: Hard gates ----------


class TestRule4HardGates(unittest.TestCase):
    def test_hitl_without_gate_fails(self):
        text = textwrap.dedent("""
            ### Step 1 — Read
            Read the input.

            ### Step 2 — Ask
            Ask the user for confirmation.

            ### Step 3 — Write
            Write the output.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        self.assertFalse(result.passed)
        self.assertTrue(any("Do NOT proceed" in f for f in result.fails), result.fails)

    def test_hitl_with_gate_passes(self):
        result = pl.lint(GOOD_WITH_HITL, has_hitl=True, invokes_skills=True)
        gate_fails = [f for f in result.fails if "Do NOT proceed" in f]
        self.assertEqual(gate_fails, [], result.fails)

    def test_no_hitl_gate_not_required(self):
        # Same text without --hitl → no gate required → should pass rule 4
        text = textwrap.dedent("""
            ### Step 1 — Read
            Read.

            ### Step 2 — Write
            Write.

            ### Step 3 — Print
            Print the output path.
        """).strip()
        result = pl.lint(text, has_hitl=False)
        gate_fails = [f for f in result.fails if "Do NOT proceed" in f]
        self.assertEqual(gate_fails, [], result.fails)


# ---------- Rule 5: Numbered questions ----------


class TestRule5NumberedQuestions(unittest.TestCase):
    def test_unnumbered_question_fails(self):
        text = textwrap.dedent("""
            ### Step 1 — Ask
            What is the target audience?

            ### Step 2 — Write
            Write the result.

            Do NOT proceed until the question is answered.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        self.assertTrue(any("not numbered" in f for f in result.fails), result.fails)

    def test_numbered_question_passes(self):
        text = textwrap.dedent("""
            ### Step 1 — Ask
            Answer the following before proceeding:
            1. What is the target audience?
            2. What is the deadline?

            ### Step 2 — Write
            Write the result.

            Do NOT proceed until all questions answered.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        q_fails = [f for f in result.fails if "not numbered" in f]
        self.assertEqual(q_fails, [], result.fails)

    def test_askuserquestion_nearby_passes(self):
        text = textwrap.dedent("""
            ### Step 1 — Ask
            Invoke AskUserQuestion to pick a format.
            Which format should we use?

            ### Step 2 — Write
            Write the result.

            Do NOT proceed until format is chosen.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        q_fails = [f for f in result.fails if "not numbered" in f]
        self.assertEqual(q_fails, [], result.fails)


# ---------- Rule 6: ≤4 inline questions ----------


class TestRule6InlineQuestionCount(unittest.TestCase):
    def test_six_questions_warns(self):
        text = textwrap.dedent("""
            ### Step 1 — Ask
            Answer all six before we continue:
            1. Q one?
            2. Q two?
            3. Q three?
            4. Q four?
            5. Q five?
            6. Q six?

            ### Step 2 — Write
            Write.

            Do NOT proceed until all questions answered.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        self.assertTrue(any("scoping-questions.md" in w for w in result.warns), result.warns)

    def test_four_questions_passes(self):
        text = textwrap.dedent("""
            ### Step 1 — Ask
            Answer:
            1. Q one?
            2. Q two?
            3. Q three?
            4. Q four?

            ### Step 2 — Write
            Write.

            Do NOT proceed until answered.
        """).strip()
        result = pl.lint(text, has_hitl=True)
        warns_about_overflow = [w for w in result.warns if "scoping-questions.md" in w]
        self.assertEqual(warns_about_overflow, [], result.warns)


# ---------- End-to-end on good fixtures ----------


class TestEndToEndGood(unittest.TestCase):
    def test_good_no_hitl_passes(self):
        result = pl.lint(GOOD_NO_HITL, has_hitl=False)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_good_with_hitl_passes(self):
        result = pl.lint(GOOD_WITH_HITL, has_hitl=True, invokes_skills=True)
        self.assertTrue(result.passed, f"fails={result.fails}")


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def test_cli_passes(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(GOOD_NO_HITL)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "phase_lint.py"), p],
            capture_output=True, text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_fails_on_bad(self):
        bad = "## Procedure\n\nNo steps here.\n"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(bad)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "phase_lint.py"), p],
            capture_output=True, text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 1)

    def test_cli_hitl_flag(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(GOOD_WITH_HITL)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "phase_lint.py"), p, "--hitl", "--invokes-skills"],
            capture_output=True, text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_bad_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "phase_lint.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
