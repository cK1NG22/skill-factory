"""Unit tests for handoff_lint.py — exercises each of the 6 rules plus edge cases.

Run from skill-signed-handoff/:
    python3 -m unittest tests.test_handoff_lint -v
    python3 -m pytest tests/ -v
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
FIXTURES = REPO_SKILL / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import handoff_lint as hl  # noqa: E402


# A minimal script that passes every rule. Used as the baseline; individual
# tests damage one rule at a time to verify isolation.
GOOD_SCRIPT = textwrap.dedent('''
    #!/usr/bin/env python3
    """Minimal signed-handoff script."""
    from __future__ import annotations

    import argparse
    import hashlib
    import json
    import sys
    from pathlib import Path

    SIGNED_FIELDS = ["argument_flow", "leadlines"]


    def _load(path):
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            return 3
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return 3
        return obj


    def _subset(payload):
        missing = sorted(set(SIGNED_FIELDS) - set(payload.keys()))
        if missing:
            sys.exit(1)
        return {k: payload[k] for k in SIGNED_FIELDS}


    def compute(payload):
        subset = _subset(payload)
        encoded = json.dumps(subset, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


    def sign(p, s):
        compute(_load(p))
        return 0


    def verify(p, s):
        if compute(_load(p)) != s.read_text().strip():
            return 2
        return 0


    def _main(argv):
        parser = argparse.ArgumentParser()
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--sign", action="store_true")
        mode.add_argument("--verify", action="store_true")
        parser.add_argument("payload", type=Path)
        parser.add_argument("signature", type=Path)
        args = parser.parse_args(argv[1:])
        if args.sign:
            return sign(args.payload, args.signature)
        return verify(args.payload, args.signature)


    if __name__ == "__main__":
        sys.exit(_main(sys.argv))
''').strip()


# ---------- Baseline ----------


class TestBaselinePasses(unittest.TestCase):
    def test_good_script_passes(self):
        result = hl.lint(GOOD_SCRIPT)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_template_passes(self):
        template = (SCRIPTS / "signature-template.py").read_text(encoding="utf-8")
        result = hl.lint(template)
        self.assertTrue(result.passed, f"fails={result.fails}")


# ---------- Rule A: --sign mode ----------


class TestRuleASignMode(unittest.TestCase):
    def test_missing_sign_mode_fails(self):
        src = GOOD_SCRIPT.replace('"--sign"', '"--other"')
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule A" in f for f in result.fails), result.fails)

    def test_sign_mode_present_passes(self):
        result = hl.lint(GOOD_SCRIPT)
        rule_a = [f for f in result.fails if "Rule A" in f]
        self.assertEqual(rule_a, [], result.fails)

    def test_argparse_single_quoted_sign_passes(self):
        # argparse call with single-quoted '--sign' must also pass
        src = GOOD_SCRIPT.replace('"--sign"', "'--sign'")
        result = hl.lint(src)
        rule_a = [f for f in result.fails if "Rule A" in f]
        self.assertEqual(rule_a, [], result.fails)


# ---------- Rule B: --verify mode ----------


class TestRuleBVerifyMode(unittest.TestCase):
    def test_missing_verify_mode_fails(self):
        src = GOOD_SCRIPT.replace('"--verify"', '"--check"')
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule B" in f for f in result.fails), result.fails)

    def test_verify_mode_present_passes(self):
        result = hl.lint(GOOD_SCRIPT)
        rule_b = [f for f in result.fails if "Rule B" in f]
        self.assertEqual(rule_b, [], result.fails)


# ---------- Rule C: hashlib.sha256 ----------


class TestRuleCSha256(unittest.TestCase):
    def test_missing_import_fails(self):
        src = GOOD_SCRIPT.replace("import hashlib", "# import hashlib")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule C" in f and "import" in f for f in result.fails))

    def test_missing_sha256_call_fails(self):
        src = GOOD_SCRIPT.replace("hashlib.sha256(encoded)", "encoded")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule C" in f and "sha256" in f for f in result.fails))

    def test_wrong_algorithm_fails(self):
        # md5 is not sha256 — Rule C call check fails
        src = GOOD_SCRIPT.replace("hashlib.sha256", "hashlib.md5")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule C" in f and "sha256" in f for f in result.fails))

    def test_bare_sha256_after_from_import_passes(self):
        src = GOOD_SCRIPT.replace(
            "import hashlib", "from hashlib import sha256"
        ).replace("hashlib.sha256(encoded)", "sha256(encoded)")
        result = hl.lint(src)
        rule_c = [f for f in result.fails if "Rule C" in f]
        self.assertEqual(rule_c, [], result.fails)


# ---------- Rule D: signed-fields list ----------


class TestRuleDSignedFields(unittest.TestCase):
    def test_missing_fields_list_fails(self):
        src = GOOD_SCRIPT.replace(
            'SIGNED_FIELDS = ["argument_flow", "leadlines"]',
            'OTHER = ["argument_flow", "leadlines"]',
        )
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule D" in f and "FIELD" in f for f in result.fails))

    def test_empty_fields_list_fails(self):
        src = GOOD_SCRIPT.replace(
            '["argument_flow", "leadlines"]', "[]"
        )
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule D" in f and "empty" in f for f in result.fails))

    def test_annotated_fields_list_passes(self):
        src = GOOD_SCRIPT.replace(
            'SIGNED_FIELDS = ["argument_flow", "leadlines"]',
            'SIGNED_FIELDS: list[str] = ["argument_flow", "leadlines"]',
        )
        result = hl.lint(src)
        rule_d = [f for f in result.fails if "Rule D" in f]
        self.assertEqual(rule_d, [], result.fails)

    def test_tuple_fields_passes(self):
        src = GOOD_SCRIPT.replace(
            '["argument_flow", "leadlines"]',
            '("argument_flow", "leadlines")',
        )
        result = hl.lint(src)
        rule_d = [f for f in result.fails if "Rule D" in f]
        self.assertEqual(rule_d, [], result.fails)

    def test_non_string_field_rejected(self):
        # A list containing a non-string element is not a valid field list
        src = GOOD_SCRIPT.replace(
            '["argument_flow", "leadlines"]',
            '["argument_flow", 42]',
        )
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule D" in f for f in result.fails), result.fails)

    def test_alternate_fields_name_passes(self):
        src = GOOD_SCRIPT.replace("SIGNED_FIELDS", "HANDOFF_FIELDS")
        result = hl.lint(src)
        rule_d = [f for f in result.fails if "Rule D" in f]
        self.assertEqual(rule_d, [], result.fails)

    def test_unicode_field_name_passes(self):
        src = GOOD_SCRIPT.replace(
            '["argument_flow", "leadlines"]',
            '["argüment_flow", "lead_lïnes"]',
        )
        result = hl.lint(src)
        rule_d = [f for f in result.fails if "Rule D" in f]
        self.assertEqual(rule_d, [], result.fails)


# ---------- Rule E: exit codes 0/1/2/3 ----------


class TestRuleEExitCodes(unittest.TestCase):
    def test_all_four_reachable_passes(self):
        result = hl.lint(GOOD_SCRIPT)
        rule_e = [f for f in result.fails if "Rule E" in f]
        self.assertEqual(rule_e, [], result.fails)

    def test_missing_exit_2_fails(self):
        # Remove the `return 2` in the verify function
        src = GOOD_SCRIPT.replace("return 2", "return 0  # was 2")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("Rule E" in f and "2" in f for f in result.fails), result.fails
        )

    def test_missing_exit_3_fails(self):
        src = GOOD_SCRIPT.replace("return 3", "return 0  # was 3")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("Rule E" in f and "3" in f for f in result.fails), result.fails
        )

    def test_docstring_mention_of_exit_does_not_count(self):
        # Build a script with `sys.exit(3)` mentioned ONLY inside the docstring.
        src = textwrap.dedent('''
            """Bad script whose docstring mentions sys.exit(3) but never calls it."""
            import argparse, hashlib, json, sys
            from pathlib import Path

            SIGNED_FIELDS = ["a"]

            def _main(argv):
                parser = argparse.ArgumentParser()
                parser.add_argument("--sign", action="store_true")
                parser.add_argument("--verify", action="store_true")
                encoded = json.dumps({}, sort_keys=True).encode()
                hashlib.sha256(encoded)
                return 0

            if __name__ == "__main__":
                sys.exit(_main(sys.argv))
        ''').strip()
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("Rule E" in f and "3" in f for f in result.fails), result.fails
        )

    def test_comment_mention_of_exit_does_not_count(self):
        src = textwrap.dedent('''
            import argparse, hashlib, json, sys
            # note: sys.exit(3) is the I/O error code
            # note: sys.exit(2) is the mismatch code
            SIGNED_FIELDS = ["a"]
            def _main(argv):
                parser = argparse.ArgumentParser()
                parser.add_argument("--sign", action="store_true")
                parser.add_argument("--verify", action="store_true")
                hashlib.sha256(json.dumps({}, sort_keys=True).encode())
                return 0
            if __name__ == "__main__":
                sys.exit(_main(sys.argv))
        ''').strip()
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule E" in f for f in result.fails), result.fails)

    def test_sys_exit_literals_counted(self):
        src = textwrap.dedent('''
            import argparse, hashlib, json, sys
            SIGNED_FIELDS = ["a"]
            def _main(argv):
                if argv[1] == "--sign":
                    hashlib.sha256(json.dumps({}, sort_keys=True).encode())
                    sys.exit(0)
                if argv[1] == "--verify":
                    sys.exit(1)
                sys.exit(2)
            try:
                _main(sys.argv)
            except Exception:
                sys.exit(3)
        ''').strip()
        result = hl.lint(src)
        rule_e = [f for f in result.fails if "Rule E" in f]
        self.assertEqual(rule_e, [], result.fails)


# ---------- Rule F: canonical serialization ----------


class TestRuleFCanonicalSerialization(unittest.TestCase):
    def test_sort_keys_true_passes(self):
        result = hl.lint(GOOD_SCRIPT)
        rule_f = [f for f in result.fails if "Rule F" in f]
        self.assertEqual(rule_f, [], result.fails)

    def test_unsorted_json_dumps_fails(self):
        src = GOOD_SCRIPT.replace("sort_keys=True", "")
        # Also remove `sorted(` fallback that would otherwise satisfy the rule
        src = src.replace("sorted(set(SIGNED_FIELDS)", "(set(SIGNED_FIELDS)")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(any("Rule F" in f for f in result.fails), result.fails)

    def test_explicit_sorted_passes(self):
        # Remove sort_keys=True but keep a sorted() call — Rule F accepts either
        src = GOOD_SCRIPT.replace(", sort_keys=True", "")
        # `sorted(set(SIGNED_FIELDS) - ...)` remains — Rule F satisfied
        result = hl.lint(src)
        rule_f = [f for f in result.fails if "Rule F" in f]
        self.assertEqual(rule_f, [], result.fails)


# ---------- Edge cases ----------


class TestEdgeCases(unittest.TestCase):
    def test_syntax_error_surfaces_gracefully(self):
        src = "def broken(:\n    pass\n"
        result = hl.lint(src)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("syntax error" in f for f in result.fails), result.fails
        )

    def test_empty_file_fails_multiple_rules(self):
        result = hl.lint("")
        self.assertFalse(result.passed)
        # empty file fails A, B, C, D, F
        self.assertTrue(any("Rule A" in f for f in result.fails))
        self.assertTrue(any("Rule B" in f for f in result.fails))
        self.assertTrue(any("Rule C" in f for f in result.fails))
        self.assertTrue(any("Rule D" in f for f in result.fails))


# ---------- Fixture oracles ----------


class TestFixtureVerdicts(unittest.TestCase):
    def test_passing_fixture_lints_clean(self):
        src = (FIXTURES / "passing-signature-script.py").read_text(encoding="utf-8")
        result = hl.lint(src)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_gaps_fixture_fails_expected_rules(self):
        src = (FIXTURES / "gaps-signature-script.py").read_text(encoding="utf-8")
        result = hl.lint(src)
        self.assertFalse(result.passed)
        # Required: at least Rules B, C, D, E, F fail on this fixture
        rule_names = set()
        for f in result.fails:
            for rule in ("Rule A", "Rule B", "Rule C", "Rule D", "Rule E", "Rule F"):
                if rule in f:
                    rule_names.add(rule)
        for expected in ("Rule B", "Rule C", "Rule D", "Rule E", "Rule F"):
            self.assertIn(expected, rule_names, f"expected {expected} in {rule_names}")


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def _run(self, text: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(text)
            p = f.name
        try:
            args = [sys.executable, str(SCRIPTS / "handoff_lint.py"), p]
            if extra_args:
                args.extend(extra_args)
            return subprocess.run(args, capture_output=True, text=True)
        finally:
            Path(p).unlink()

    def test_cli_passes(self):
        result = self._run(GOOD_SCRIPT)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_fails_on_broken(self):
        src = GOOD_SCRIPT.replace('"--verify"', '"--nope"')
        result = self._run(src)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertFalse(data["passed"])

    def test_cli_bad_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff_lint.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_file_not_found(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff_lint.py"),
             "/tmp/__does_not_exist_handoff_lint_test__.py"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff_lint.py"), "-"],
            input=GOOD_SCRIPT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
