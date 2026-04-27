#!/usr/bin/env python3
"""skill-compliance-gate orchestrator.

Two modes:
  --input <input.md>        factory-driven. Writes output.md or notes.md next
                            to input.md; exits 0 (pass) or 1 (fail).
  --skill <skill-dir>       standalone. Prints JSON to stdout; exits 0/1.

Pure stdlib, no external dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


META_BP_SLUGS = [
    "bp-018", "bp-025", "bp-026", "bp-027", "bp-028",
    "bp-029", "bp-030", "bp-031", "bp-032", "bp-033", "bp-034",
]
META_BP_PATTERN = re.compile(
    r"\bpatterns/meta/bp-\d{3}\b|\b(?:" + "|".join(META_BP_SLUGS) + r")\b",
    re.IGNORECASE,
)

COMPLIANCE_CHECK_PATH = (
    Path.home() / ".claude" / "skills" / "skill-compliance"
    / "scripts" / "compliance_check.py"
)


def parse_input_md(path: Path) -> dict:
    """Extract `key: value` fields from the driver-materialized pack.

    The pack uses a simple markdown with `**key**: value` or `- **key**: value`
    lines. We accept either form. Returns {} on unreadable input.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(
            r"^\s*(?:-\s+)?\*\*([a-z_][a-z0-9_]*)\*\*\s*:\s*(.+?)\s*$",
            line,
        )
        if m:
            fields.setdefault(m.group(1), m.group(2).strip("`").strip())
    return fields


def run_checker(skill_path: Path) -> dict:
    """Subprocess-call compliance_check.py and parse its JSON."""
    result = subprocess.run(
        [sys.executable, str(COMPLIANCE_CHECK_PATH), str(skill_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(
            f"compliance_check.py exited {result.returncode}: "
            f"{result.stderr.strip().splitlines()[0] if result.stderr.strip() else 'no stderr'}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"compliance_check.py returned unparseable output — {exc}"
        ) from exc


def collect_scan_files(skill_path: Path) -> list[Path]:
    """Files Check 14 scans: SKILL.md + references/* (one level) +
    phases/*/director.md + phases/*/references/* (one level).
    """
    files: list[Path] = []
    skill_md = skill_path / "SKILL.md"
    if skill_md.is_file():
        files.append(skill_md)

    refs = skill_path / "references"
    if refs.is_dir():
        for p in sorted(refs.iterdir()):
            if p.is_file():
                files.append(p)

    phases = skill_path / "phases"
    if phases.is_dir():
        for phase_dir in sorted(phases.iterdir()):
            if not phase_dir.is_dir():
                continue
            director = phase_dir / "director.md"
            if director.is_file():
                files.append(director)
            phase_refs = phase_dir / "references"
            if phase_refs.is_dir():
                for p in sorted(phase_refs.iterdir()):
                    if p.is_file():
                        files.append(p)
    return files


def check_14_meta_citations(skill_path: Path) -> list[dict]:
    """Scan the assembled skill for `patterns/meta/bp-NNN` paths or meta-BP
    slugs (bp-018, bp-025..034). Returns a list of hit dicts.
    """
    hits: list[dict] = []
    for file in collect_scan_files(skill_path):
        try:
            text = file.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in META_BP_PATTERN.finditer(line):
                hits.append({
                    "file": str(file.relative_to(skill_path)),
                    "line": lineno,
                    "matched": m.group(0).lower(),
                })
    return hits


def required_fails(checker_json: dict) -> list[dict]:
    """Extract required-severity FAILs from the checker's JSON."""
    fails: list[dict] = []
    for result in checker_json.get("results", []):
        for check in result.get("checks", []):
            if check.get("severity") == "required" and check.get("status") == "fail":
                fails.append({
                    "id": check.get("id"),
                    "name": check.get("name"),
                    "message": check.get("message"),
                })
    return fails


def evaluate(skill_path: Path) -> dict:
    """Run the gate: checker core + Check 14. Returns the verdict dict."""
    if not skill_path.is_dir():
        return {
            "verdict": "fail",
            "blocker": f"assembled skill not found at {skill_path}",
            "checker_fails": [],
            "check_14_hits": [],
        }
    if not COMPLIANCE_CHECK_PATH.exists():
        return {
            "verdict": "fail",
            "blocker": f"skill-compliance not installed at {COMPLIANCE_CHECK_PATH}",
            "checker_fails": [],
            "check_14_hits": [],
        }
    try:
        checker_json = run_checker(skill_path)
    except RuntimeError as exc:
        return {
            "verdict": "fail",
            "blocker": str(exc),
            "checker_fails": [],
            "check_14_hits": [],
        }
    checker_fails = required_fails(checker_json)
    hits = check_14_meta_citations(skill_path)

    if checker_fails or hits:
        parts = []
        if checker_fails:
            parts.append(
                f"{len(checker_fails)} required-tier check(s) failed: "
                + ", ".join(f"#{f['id']} {f['name']}" for f in checker_fails)
            )
        if hits:
            parts.append(
                f"{len(hits)} Check 14 meta-BP citation(s): "
                + ", ".join(f"{h['file']}:{h['line']} ({h['matched']})" for h in hits[:5])
                + (" ..." if len(hits) > 5 else "")
            )
        return {
            "verdict": "fail",
            "blocker": "compliance gate failed — " + "; ".join(parts),
            "checker_fails": checker_fails,
            "check_14_hits": hits,
            "checker_summary": summarize(checker_json),
        }
    return {
        "verdict": "pass",
        "blocker": None,
        "checker_fails": [],
        "check_14_hits": [],
        "checker_summary": summarize(checker_json),
    }


def summarize(checker_json: dict) -> dict:
    """One-line summary for the output.md table."""
    if not checker_json.get("results"):
        return {"passed": 0, "warnings": 0, "failures": 0, "total": 0, "info": 0}
    result = checker_json["results"][0]
    summary = result.get("summary", {})
    info = sum(1 for c in result.get("checks", []) if c.get("status") == "info")
    return {
        "passed": summary.get("passed", 0),
        "warnings": summary.get("warnings", 0),
        "failures": summary.get("failures", 0),
        "info": info,
        "total": summary.get("total", 0),
        "skill_name": result.get("skill_name"),
    }


def write_pass_output(phase_dir: Path, verdict: dict, skill_path: Path) -> None:
    """Write output.md summarizing a PASS verdict."""
    s = verdict.get("checker_summary", {})
    lines = [
        "# skill-compliance-gate — PASS",
        "",
        f"Assembled skill: `{skill_path}`",
        "",
        "| Tier        | Pass | Warn | Fail | Info |",
        "|-------------|------|------|------|------|",
        f"| 13 checks   | {s.get('passed', 0)} | {s.get('warnings', 0)} | {s.get('failures', 0)} | {s.get('info', 0)} |",
        f"| Check 14    | 1    | 0    | 0    | 0    |",
        "",
        "Gate verdict: **pass**.",
        "",
    ]
    (phase_dir / "output.md").write_text("\n".join(lines), encoding="utf-8")


def write_fail_notes(phase_dir: Path, verdict: dict) -> None:
    """Write notes.md with the BLOCKER line."""
    line = f"BLOCKER: {verdict['blocker']}"
    (phase_dir / "notes.md").write_text(line + "\n", encoding="utf-8")


def main_driver(input_path: Path) -> int:
    """--input mode. Writes to phase dir; returns exit code."""
    phase_dir = input_path.parent
    fields = parse_input_md(input_path)
    if not input_path.exists():
        phase_dir.mkdir(parents=True, exist_ok=True)
        (phase_dir / "notes.md").write_text(
            f"BLOCKER: input.md not found at {input_path}\n", encoding="utf-8"
        )
        return 1
    assembled = fields.get("assembled_skill_path")
    if not assembled:
        write_fail_notes(phase_dir, {
            "blocker": "skill-compliance-gate input.md is malformed — field "
                       "assembled_skill_path missing"
        })
        return 1
    skill_path = Path(assembled).expanduser()
    verdict = evaluate(skill_path)
    if verdict["verdict"] == "pass":
        write_pass_output(phase_dir, verdict, skill_path)
        return 0
    write_fail_notes(phase_dir, verdict)
    return 1


def main_standalone(skill_path: Path) -> int:
    """--skill mode. Prints JSON to stdout; returns exit code."""
    verdict = evaluate(skill_path)
    print(json.dumps(verdict, indent=2, default=str))
    return 0 if verdict["verdict"] == "pass" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="skill-compliance-gate orchestrator")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=Path, help="driver-materialized input.md path")
    mode.add_argument("--skill", type=Path, help="standalone: assembled skill dir")
    args = parser.parse_args(argv)
    if args.input:
        return main_driver(args.input)
    return main_standalone(args.skill)


if __name__ == "__main__":
    sys.exit(main())
