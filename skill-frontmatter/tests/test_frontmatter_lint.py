"""Unit tests for frontmatter_lint.py — exercises each of the 5 rules.

Run from skill-frontmatter/:
    python3 -m unittest tests.test_frontmatter_lint -v
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
import frontmatter_lint as fl  # noqa: E402


def _fm(yaml: str) -> str:
    """Wrap a raw YAML body in frontmatter delimiters."""
    return f"---\n{textwrap.dedent(yaml).strip()}\n---\n"


GOOD_YAML = _fm(
    """
    name: acme-board-memo
    description: >-
      Generates a formatted .docx board memo from a markdown outline using
      Acme's cover page. Use when "generate board memo", "board memo from
      this", "make a board memo", "turn this into a board memo", "render as
      board memo". Do NOT use for generic markdown conversion.
    argument-hint: "<path-to-markdown>"
    allowed-tools:
      - Read
      - Write
      - Agent
    """
)


class TestExtractFrontmatter(unittest.TestCase):
    def test_extracts_between_delimiters(self):
        doc = "---\nname: foo\n---\n\n# body\n"
        self.assertEqual(fl.extract_frontmatter(doc), "name: foo")

    def test_missing_opening_delimiter_returns_none(self):
        self.assertIsNone(fl.extract_frontmatter("# just a heading\n"))

    def test_missing_closing_delimiter_returns_none(self):
        self.assertIsNone(fl.extract_frontmatter("---\nname: foo\n# body\n"))


class TestGoodFrontmatter(unittest.TestCase):
    def test_passes_cleanly(self):
        fm = fl.extract_frontmatter(GOOD_YAML)
        result = fl.lint(fm)
        self.assertTrue(result.passed, f"fails={result.fails}")
        self.assertEqual(result.fails, [])


class TestRule1Name(unittest.TestCase):
    def _lint_name(self, name: str) -> fl.LintResult:
        return fl.lint(GOOD_YAML.replace("acme-board-memo", name).split("---\n")[1])

    def test_uppercase_fails(self):
        result = fl.lint(_fm("""
            name: Acme-Board
            description: one two three four five six seven eight nine ten eleven twelve. Use when "a b", "c d", "e f", "g h". Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("^[a-z]" in f for f in result.fails), result.fails)

    def test_underscore_fails(self):
        result = fl.lint(_fm("""
            name: acme_board
            description: one two three four five six seven eight nine ten eleven twelve. Use when "a b", "c d", "e f", "g h". Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("^[a-z]" in f for f in result.fails), result.fails)

    def test_leading_digit_fails(self):
        result = fl.lint(_fm("""
            name: 1acme
            description: one two three four five six seven eight nine ten eleven twelve. Use when "a b", "c d", "e f", "g h". Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)

    def test_reserved_name_fails(self):
        result = fl.lint(_fm("""
            name: claude
            description: one two three four five six seven eight nine ten eleven twelve. Use when "a b", "c d", "e f", "g h". Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("reserved" in f for f in result.fails), result.fails)

    def test_too_long_fails(self):
        long_name = "a" + "-".join(["x"] * 40)  # way over 64 chars
        result = fl.lint(_fm(f"""
            name: {long_name}
            description: one two three four five six seven eight nine ten eleven twelve. Use when "a b", "c d", "e f", "g h". Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)


class TestRule2DescriptionLength(unittest.TestCase):
    def test_too_short_fails(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: short.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("too terse" in f or "min 80" in f for f in result.fails), result.fails)

    def test_too_long_fails(self):
        long_desc = "x " * 600  # ~1200 chars, over 1024
        result = fl.lint(_fm(f"""
            name: acme-x
            description: {long_desc}
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("max 1024" in f for f in result.fails), result.fails)


class TestRule3TriggerPhrases(unittest.TestCase):
    def test_fewer_than_three_phrases_fails(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: This is a long enough description that passes rule 2 but only includes "one phrase" in quotes so rule 3 should fail because we need at least three phrases with spaces.
            allowed-tools:
              - Read
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("trigger phrase" in f for f in result.fails), result.fails)

    def test_three_or_more_phrases_passes_rule3(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: This is long enough and includes "phrase one", "phrase two", and "phrase three" as three quoted trigger phrases so rule 3 passes. Do NOT use for foo.
            allowed-tools:
              - Read
            """))
        # rule 3 fine; warning about 3-4 phrases is expected (factory target is 5+)
        rule3_failures = [f for f in result.fails if "trigger phrase" in f]
        self.assertEqual(rule3_failures, [], rule3_failures)


class TestRule4AllowedTools(unittest.TestCase):
    def test_missing_fails(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "a b", "c d", "e f" trigger phrases. Do NOT use for foo.
            """))
        self.assertFalse(result.passed)
        self.assertTrue(any("allowed-tools" in f for f in result.fails), result.fails)

    def test_unknown_tool_warns_but_passes(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "a b", "c d", "e f" trigger phrases. Do NOT use for foo.
            allowed-tools:
              - Read
              - SomeCustomMadeUpTool
            """))
        self.assertTrue(result.passed, result.fails)
        self.assertTrue(any("unrecognized" in w for w in result.warns), result.warns)

    def test_mcp_tool_accepted(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "a b", "c d", "e f" trigger phrases. Do NOT use for foo.
            allowed-tools:
              - Read
              - mcp__some_server__some_tool
            """))
        self.assertTrue(result.passed)
        self.assertFalse(any("unrecognized" in w for w in result.warns), result.warns)


class TestRule5NegativeClause(unittest.TestCase):
    def test_missing_negative_clause_warns(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "phrase one", "phrase two", "phrase three" as trigger phrases but without any negative clause.
            allowed-tools:
              - Read
            """))
        self.assertTrue(result.passed, result.fails)
        self.assertTrue(any("negative clause" in w for w in result.warns), result.warns)

    def test_do_not_use_for_accepted(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "phrase one", "phrase two", "phrase three" triggers. Do NOT use for bad cases.
            allowed-tools:
              - Read
            """))
        self.assertFalse(any("negative clause" in w for w in result.warns), result.warns)

    def test_do_not_use_to_accepted(self):
        result = fl.lint(_fm("""
            name: acme-x
            description: Long enough description with "phrase one", "phrase two", "phrase three" triggers. Do NOT use to break things.
            allowed-tools:
              - Read
            """))
        self.assertFalse(any("negative clause" in w for w in result.warns), result.warns)


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def test_cli_passes_good_frontmatter(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(GOOD_YAML)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "frontmatter_lint.py"), p],
            capture_output=True,
            text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_fails_bad_frontmatter(self):
        bad = _fm("""
            name: BADNAME
            description: too short
            """)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(bad)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "frontmatter_lint.py"), p],
            capture_output=True,
            text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 1)  # lint failure exit code
        data = json.loads(result.stdout)
        self.assertFalse(data["passed"])

    def test_cli_bad_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "frontmatter_lint.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
