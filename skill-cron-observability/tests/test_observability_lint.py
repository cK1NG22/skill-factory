"""Unit tests for observability_lint.py — exercises each of the 4 BP-022 rules.

Run from skill-cron-observability/:
    python3 -m unittest tests.test_observability_lint -v
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

sys.path.insert(0, str(SCRIPTS))
import observability_lint as obl  # noqa: E402


# --- Reference good snippets ---

GOOD_SNIPPET_PY = textwrap.dedent('''
    import json
    import os
    from datetime import datetime
    from pathlib import Path

    SLUG = "acme-weekly-digest"
    EXT = "md"

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    home = Path.home() / "Claude" / SLUG
    run_dir = home / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = run_dir / f"artifact.{EXT}"
    artifact_path.write_text("digest body")
    success = True

    result = {
        "last_run": datetime.utcnow().isoformat() + "Z",
        "success": success,
        "artifact_path": str(artifact_path.resolve()),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2))

    latest = home / "latest.json"
    tmp = home / "latest.json.tmp"
    if tmp.exists() or tmp.is_symlink():
        tmp.unlink()
    tmp.symlink_to(run_dir / "result.json")
    os.replace(tmp, latest)
''').strip()


GOOD_SNIPPET_MD = textwrap.dedent(f'''
    # Instrumentation snippet

    ```python
    {GOOD_SNIPPET_PY}
    ```
''').strip()


# ---------- Rule A: result.json under runs/<timestamp>/ ----------


class TestRuleAResultJson(unittest.TestCase):
    def test_good_snippet_passes_rule_a(self):
        result = obl.lint(GOOD_SNIPPET_PY)
        rule_a_fails = [f for f in result.fails if f.startswith("Rule A")]
        self.assertEqual(rule_a_fails, [], result.fails)

    def test_missing_result_json_fails(self):
        code = textwrap.dedent('''
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().isoformat()
            run_dir = Path("~/Claude/x/runs") / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "status.json").write_text("{}")
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(
            any("Rule A" in f and "result.json" in f for f in result.fails),
            result.fails,
        )

    def test_missing_runs_dir_fails(self):
        code = textwrap.dedent('''
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().isoformat()
            Path("~/Claude/x/status/result.json").write_text("{}")
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(
            any("Rule A" in f and "runs/" in f for f in result.fails),
            result.fails,
        )

    def test_missing_timestamp_fails(self):
        code = textwrap.dedent('''
            from pathlib import Path
            run_dir = Path("~/Claude/x/runs/constant-name")
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "result.json").write_text('{"last_run":"x","success":true,"artifact_path":"y"}')
            (run_dir / "artifact.md").write_text("body")
            latest = Path("~/Claude/x/latest.json")
            import os
            os.symlink(run_dir / "result.json", latest)
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(
            any("Rule A" in f and "timestamp" in f for f in result.fails),
            result.fails,
        )


# ---------- Rule B: artifact file written ----------


class TestRuleBArtifact(unittest.TestCase):
    def test_good_snippet_passes_rule_b(self):
        result = obl.lint(GOOD_SNIPPET_PY)
        rule_b_fails = [f for f in result.fails if f.startswith("Rule B")]
        self.assertEqual(rule_b_fails, [], result.fails)

    def test_missing_artifact_fails(self):
        code = textwrap.dedent('''
            import json
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            result = {"last_run": ts, "success": True, "artifact_path": ""}
            (run_dir / "result.json").write_text(json.dumps(result))
            # No artifact write at all
            latest = Path.home() / "Claude" / "x" / "latest.json"
            import os
            os.symlink(run_dir / "result.json", latest)
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(
            any("Rule B" in f for f in result.fails),
            result.fails,
        )

    def test_artifact_literal_accepted(self):
        # Writes a file named "artifact.csv"; Rule B passes via literal match.
        code = textwrap.dedent('''
            import json
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            with open(run_dir / "artifact.csv", "w") as f:
                f.write("a,b\\n1,2\\n")
            result = {"last_run": ts, "success": True, "artifact_path": str(run_dir / "artifact.csv")}
            (run_dir / "result.json").write_text(json.dumps(result))
            import os
            latest = Path.home() / "Claude" / "x" / "latest.json"
            os.symlink(run_dir / "result.json", latest)
        ''').strip()
        result = obl.lint(code)
        rule_b_fails = [f for f in result.fails if f.startswith("Rule B")]
        self.assertEqual(rule_b_fails, [], result.fails)


# ---------- Rule C: latest.json pointer ----------


class TestRuleCLatest(unittest.TestCase):
    def test_good_snippet_passes_rule_c(self):
        result = obl.lint(GOOD_SNIPPET_PY)
        rule_c_fails = [f for f in result.fails if f.startswith("Rule C")]
        self.assertEqual(rule_c_fails, [], result.fails)

    def test_missing_latest_fails(self):
        code = textwrap.dedent('''
            import json
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact.md").write_text("body")
            result = {"last_run": ts, "success": True, "artifact_path": "x"}
            (run_dir / "result.json").write_text(json.dumps(result))
            # No latest.json pointer maintained
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(
            any("Rule C" in f for f in result.fails),
            result.fails,
        )

    def test_latest_without_symlink_warns(self):
        code = textwrap.dedent('''
            import json
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact.md").write_text("body")
            result = {"last_run": ts, "success": True, "artifact_path": "x"}
            (run_dir / "result.json").write_text(json.dumps(result))
            # Copy (not symlink) to latest.json
            latest = Path.home() / "Claude" / "x" / "latest.json"
            latest.write_text(json.dumps(result))
        ''').strip()
        result = obl.lint(code)
        rule_c_fails = [f for f in result.fails if f.startswith("Rule C")]
        self.assertEqual(rule_c_fails, [], result.fails)
        self.assertTrue(
            any("Rule C" in w and "symlink" in w for w in result.warns),
            result.warns,
        )


# ---------- Rule D: result.json keys ----------


class TestRuleDKeys(unittest.TestCase):
    def test_good_snippet_passes_rule_d(self):
        result = obl.lint(GOOD_SNIPPET_PY)
        rule_d_fails = [f for f in result.fails if f.startswith("Rule D")]
        self.assertEqual(rule_d_fails, [], result.fails)

    def test_missing_last_run_fails(self):
        code = GOOD_SNIPPET_PY.replace('"last_run"', '"ran_at"')
        result = obl.lint(code)
        self.assertTrue(
            any("Rule D" in f and "last_run" in f for f in result.fails),
            result.fails,
        )

    def test_missing_success_fails(self):
        code = GOOD_SNIPPET_PY.replace('"success"', '"ok"')
        result = obl.lint(code)
        self.assertTrue(
            any("Rule D" in f and "success" in f for f in result.fails),
            result.fails,
        )

    def test_missing_artifact_path_fails(self):
        code = GOOD_SNIPPET_PY.replace('"artifact_path"', '"output_path"')
        result = obl.lint(code)
        self.assertTrue(
            any("Rule D" in f and "artifact_path" in f for f in result.fails),
            result.fails,
        )

    def test_all_three_keys_missing_lists_all(self):
        code = GOOD_SNIPPET_PY
        code = code.replace('"last_run"', '"ran_at"')
        code = code.replace('"success"', '"ok"')
        code = code.replace('"artifact_path"', '"output_path"')
        result = obl.lint(code)
        rule_d_fails = [f for f in result.fails if f.startswith("Rule D")]
        self.assertEqual(len(rule_d_fails), 1)
        self.assertIn("last_run", rule_d_fails[0])
        self.assertIn("success", rule_d_fails[0])
        self.assertIn("artifact_path", rule_d_fails[0])


# ---------- Edge cases ----------


class TestEdgeCases(unittest.TestCase):
    def test_empty_code_fails(self):
        result = obl.lint("")
        self.assertFalse(result.passed)
        self.assertTrue(any("empty" in f for f in result.fails), result.fails)

    def test_markdown_without_fences_fails_targeted(self):
        # Prose-only markdown with no ```python block.
        result = obl.lint("", had_fences=False)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("no fenced" in f for f in result.fails), result.fails
        )

    def test_multiple_fenced_blocks_concatenated(self):
        """A markdown file with TWO fenced python blocks: one satisfies A+B,
        the other satisfies C+D. Concatenation must pass."""
        md = textwrap.dedent(f'''
            # First block writes result.json and artifact

            ```python
            import json
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact.md").write_text("body")
            result = {{"last_run": ts, "success": True, "artifact_path": str(run_dir / "artifact.md")}}
            (run_dir / "result.json").write_text(json.dumps(result))
            ```

            # Second block updates latest.json

            ```python
            import os
            from pathlib import Path
            latest = Path.home() / "Claude" / "x" / "latest.json"
            latest.symlink_to(run_dir / "result.json")
            ```
        ''').strip()
        blocks = obl._FENCED_PYTHON_BLOCK.findall(md)
        self.assertEqual(len(blocks), 2)
        code = "\n\n".join(blocks)
        result = obl.lint(code, had_fences=True)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_unicode_skill_name_passes(self):
        """Skill slug can contain non-ASCII characters (emoji, accents).
        The lint does not inspect the slug itself — it inspects the structural
        keys/paths/literals."""
        code = GOOD_SNIPPET_PY.replace(
            '"acme-weekly-digest"', '"café-digëst-週報"'
        )
        result = obl.lint(code)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_single_quotes_accepted(self):
        """String literals may use single quotes, double quotes, or a mix."""
        code = textwrap.dedent('''
            import json
            import os
            from datetime import datetime
            from pathlib import Path
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            run_dir = Path.home() / 'Claude' / 'x' / 'runs' / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / 'artifact.md').write_text('body')
            result = {'last_run': ts, 'success': True, 'artifact_path': 'x'}
            (run_dir / 'result.json').write_text(json.dumps(result))
            latest = Path.home() / 'Claude' / 'x' / 'latest.json'
            os.symlink(run_dir / 'result.json', latest)
        ''').strip()
        result = obl.lint(code)
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_docstring_literals_count_documented_false_positive(self):
        """The lint searches for STRING LITERALS. A docstring containing the
        exact literals "result.json", "latest.json", "last_run" etc. is still
        a string match. This is a DOCUMENTED false-positive surface — users
        who paste the BP-022 doc verbatim as a docstring get false credit.
        The test pins the behavior so future refactors notice."""
        code = textwrap.dedent('''
            """Wire up:
            - "result.json" under runs/<timestamp>/
            - "artifact.md" alongside
            - "latest.json" symlink
            - "last_run", "success", "artifact_path" keys
            - call datetime.utcnow()
            """
            pass
        ''').strip()
        result = obl.lint(code)
        # All 4 rules "pass" because the quoted literals exist somewhere.
        self.assertTrue(result.passed, f"fails={result.fails}")

    def test_comment_without_quotes_does_not_count(self):
        """A bare comment mentioning `result.json` (no quotes) must NOT
        satisfy Rule A. The regexes require quote delimiters."""
        code = textwrap.dedent('''
            # TODO: wire up result.json, latest.json, last_run, etc.
            pass
        ''').strip()
        result = obl.lint(code)
        self.assertFalse(result.passed, f"fails={result.fails}")


class TestFixtures(unittest.TestCase):
    def test_passing_snippet_fixture_lints_clean(self):
        fixture = REPO_SKILL / "fixtures" / "passing-snippet.md"
        text = fixture.read_text(encoding="utf-8")
        blocks = obl._FENCED_PYTHON_BLOCK.findall(text)
        self.assertTrue(blocks, "fixture must contain at least one ```python block")
        code = "\n\n".join(blocks)
        result = obl.lint(code, had_fences=True)
        self.assertTrue(result.passed, f"fails={result.fails}")


# ---------- CLI integration ----------


class TestCLI(unittest.TestCase):
    def test_cli_passes_on_good_snippet(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(GOOD_SNIPPET_MD)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "observability_lint.py"), p],
            capture_output=True, text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])

    def test_cli_fails_on_bad_snippet(self):
        bad = textwrap.dedent('''
            # Broken snippet — missing latest.json

            ```python
            from pathlib import Path
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            run_dir = Path.home() / "Claude" / "x" / "runs" / ts
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact.md").write_text("body")
            (run_dir / "result.json").write_text('{"last_run":"x","success":true,"artifact_path":"y"}')
            ```
        ''').strip()
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(bad)
            p = f.name
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "observability_lint.py"), p],
            capture_output=True, text=True,
        )
        Path(p).unlink()
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertFalse(data["passed"])
        self.assertTrue(
            any("Rule C" in f for f in data["fails"]), data["fails"]
        )

    def test_cli_bad_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "observability_lint.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_nonexistent_path(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "observability_lint.py"),
             "/nonexistent/path/does/not/exist.md"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_stdin_mode(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "observability_lint.py"), "-"],
            input=GOOD_SNIPPET_MD,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["passed"])


if __name__ == "__main__":
    unittest.main()
