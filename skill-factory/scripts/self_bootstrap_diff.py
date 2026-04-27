#!/usr/bin/env python3
"""
self_bootstrap_diff.py — Stage 9c structural diff for the factory's
self-bootstrap acceptance criterion (Principle D).

Compares the artifacts produced by a self-bootstrap factory run (scratch
dir) against the committed `skill-factory/` tree. Reports structural
equivalence per the plan v2 tiebreaker rule: committed code is
authoritative; spec divergence updates the spec, not the code.

Usage:
    self_bootstrap_diff.py <scratch-dir> <committed-skill-dir>

Where:
    <scratch-dir> contains the factory's per-phase outputs
        (phases/03-skill-frontmatter/output.yaml, phases/04-.../output.md,
        phases/05-.../output.md, scaffolded-skill/ tree).
    <committed-skill-dir> is the canonical `skill-factory/` source tree.

Reports (JSON):
    fired_phases   — which phase dirs have non-empty input.md (i.e., were
                     materialized by the driver)
    artifacts      — per-fired-phase: which expected output files exist
    lint_verdicts  — per-fired-phase: lint result on the artifact
    section_match  — generated frontmatter vs committed frontmatter (name,
                     description-length, trigger-phrase count, allowed-tools
                     count); generated Procedure step count vs committed
    deltas         — file-count delta (scratch generated artifacts vs
                     committed file count of equivalent files)
    verdict        — "pass" | "divergence" | "fail"

Exit codes:
    0 — verdict pass (all expected sub-skills fired, all lints green,
        section sets match within tolerance)
    1 — verdict divergence (something fired/missing or lint fail; diff
        report shows what to reconcile per tiebreaker)
    2 — verdict fail / usage error
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# Map phase dir name -> (artifact filename, lint command template).
# Lint command uses {artifact} as placeholder for the artifact path.
_LINT_COMMANDS: dict[str, tuple[str, list[str]]] = {
    "03-skill-frontmatter": (
        "output.yaml",
        ["python3", "{REPO}/skill-frontmatter/scripts/frontmatter_lint.py", "{artifact}"],
    ),
    "04-skill-phase-designer": (
        "output.md",
        ["python3", "{REPO}/skill-phase-designer/scripts/phase_lint.py", "{artifact}"],
    ),
    "05-skill-references-scaffolder": (
        # The refs sub-skill emits output.md; lint targets the scaffolded tree
        "output.md",
        None,  # Lint command resolved at runtime against scaffolded-skill/ dir
    ),
}


def _detect_repo_root(committed_skill_dir: Path) -> Path:
    """The committed skill dir lives under <repo>/skill-factory/. Walk up to
    find a `patterns/` sibling — that's the repo root."""
    p = committed_skill_dir.resolve()
    for ancestor in [p] + list(p.parents):
        if (ancestor / "patterns").is_dir() and (ancestor / "skill-factory").is_dir():
            return ancestor
    raise FileNotFoundError(
        f"could not locate factory repo root from {committed_skill_dir}"
    )


def detect_fired_phases(scratch: Path) -> list[str]:
    """A phase fired if scratch/phases/<name>/input.md exists and is non-empty."""
    phases_dir = scratch / "phases"
    if not phases_dir.is_dir():
        return []
    fired = []
    for child in sorted(phases_dir.iterdir()):
        if not child.is_dir():
            continue
        input_md = child / "input.md"
        if input_md.is_file() and input_md.stat().st_size > 0:
            fired.append(child.name)
    return fired


def check_artifact(scratch: Path, phase_name: str) -> dict:
    """Verify the expected artifact for a phase exists and run its lint."""
    if phase_name not in _LINT_COMMANDS:
        return {"phase": phase_name, "expected_artifact": None, "exists": False,
                "lint": "unknown phase"}

    artifact_name, lint_template = _LINT_COMMANDS[phase_name]
    phase_dir = scratch / "phases" / phase_name
    artifact_path = phase_dir / artifact_name
    result = {
        "phase": phase_name,
        "expected_artifact": artifact_name,
        "exists": artifact_path.is_file(),
    }

    if not artifact_path.is_file():
        result["lint"] = "skipped (artifact missing)"
        return result

    repo = _detect_repo_root(Path(sys.argv[2])) if len(sys.argv) > 2 else None

    if phase_name == "05-skill-references-scaffolder":
        # Lint the scaffolded tree (not the plan output)
        scaffolded = scratch / "scaffolded-skill"
        if not scaffolded.is_dir():
            result["lint"] = "skipped (scaffolded-skill/ tree missing)"
            return result
        cmd = ["python3", str(repo / "skill-references-scaffolder" / "scripts" / "references_lint.py"),
               str(scaffolded), "--has-references"]
    else:
        cmd = [arg.replace("{REPO}", str(repo)).replace("{artifact}", str(artifact_path))
               for arg in lint_template]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        if proc.stdout.strip():
            try:
                lint_json = json.loads(proc.stdout.strip())
                result["lint"] = {
                    "passed": lint_json.get("passed", False),
                    "fails_count": len(lint_json.get("fails", [])),
                    "warns_count": len(lint_json.get("warns", [])),
                }
            except json.JSONDecodeError:
                result["lint"] = {"raw_stdout": proc.stdout.strip()[:200]}
        else:
            result["lint"] = {"exit_code": proc.returncode, "stderr": proc.stderr.strip()[:200]}
    except subprocess.TimeoutExpired:
        result["lint"] = "timeout"

    return result


def section_match(scratch: Path, committed_skill_dir: Path) -> dict:
    """Compare generated frontmatter + Procedure shape against committed."""
    out = {}

    # Frontmatter: name, description length, trigger phrase count, allowed-tools count
    gen_yaml = scratch / "phases" / "03-skill-frontmatter" / "output.yaml"
    com_skill = committed_skill_dir / "SKILL.md"
    if gen_yaml.is_file() and com_skill.is_file():
        gen = _parse_simple_yaml(gen_yaml.read_text(encoding="utf-8"))
        com = _parse_skill_md_frontmatter(com_skill.read_text(encoding="utf-8"))
        out["frontmatter"] = {
            "generated": _summarize_frontmatter(gen),
            "committed": _summarize_frontmatter(com),
            "name_match": gen.get("name") == com.get("name"),
        }

    # Procedure: count of `### Step N` headings in generated phase-04 vs committed SKILL.md
    gen_proc = scratch / "phases" / "04-skill-phase-designer" / "output.md"
    if gen_proc.is_file() and com_skill.is_file():
        gen_steps = _count_step_headings(gen_proc.read_text(encoding="utf-8"))
        com_steps = _count_step_headings(com_skill.read_text(encoding="utf-8"))
        out["procedure"] = {
            "generated_step_count": gen_steps,
            "committed_step_count": com_steps,
            "delta": gen_steps - com_steps,
            "within_tolerance": abs(gen_steps - com_steps) <= 1,
        }

    return out


def _parse_simple_yaml(text: str) -> dict:
    """Hand-rolled minimal YAML parser for frontmatter (matches the
    skill-frontmatter sub-skill's parser shape)."""
    data: dict = {}
    text = text.strip()
    if text.startswith("---"):
        text = text[3:].lstrip("\n")
    if "\n---" in text:
        text = text.split("\n---")[0]
    current_key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_key:
                data.setdefault(current_key, []).append(line[4:].strip())
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                data[key] = value
            else:
                data[key] = []
    return data


def _parse_skill_md_frontmatter(text: str) -> dict:
    """Extract frontmatter from a SKILL.md (between leading --- delimiters)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    return _parse_simple_yaml(text[: end + 4])


def _summarize_frontmatter(fm: dict) -> dict:
    desc = fm.get("description", "")
    desc_str = desc if isinstance(desc, str) else ""
    return {
        "name": fm.get("name"),
        "description_length": len(desc_str),
        "trigger_phrase_count": desc_str.lower().count('"'),
        "allowed_tools_count": len(fm.get("allowed-tools", [])) if isinstance(fm.get("allowed-tools"), list) else 0,
    }


_STEP_HEADING = re.compile(r"^###\s+Step\s+\d+", re.MULTILINE)


def _count_step_headings(text: str) -> int:
    return len(_STEP_HEADING.findall(text))


def gate_verdicts(scratch: Path, committed: Path) -> dict:
    """Stage 10c: compare gate verdicts between the regenerated assembled
    skill (at <scratch>/assembled/<slug>/) and the committed factory.

    Returns a dict with three fields:
      regenerated  — verdict for the assembled skill, or "n/a" if the
                     scratch dir doesn't have an assembled subdir (i.e.
                     the self-bootstrap pre-dates Stage 10b's Phase 8).
      committed    — verdict for the committed skill at `committed`.
      match        — True iff both verdicts are "pass". A regenerated
                     "n/a" plus committed "pass" still counts as match=True
                     for backward compatibility with pre-10b runs.

    Both gate runs use the meta-skill auto-detect path (no --meta-skill
    flag) so the marker on the SKILL.md is what gates Check 14.
    """
    repo_root = _detect_repo_root(committed)
    gate_script = repo_root / "skill-compliance-gate" / "scripts" / "gate.py"
    if not gate_script.is_file():
        return {"regenerated": "n/a", "committed": "n/a",
                "match": False, "reason": "gate.py not found"}

    def _run_gate(skill_dir: Path) -> str:
        try:
            proc = subprocess.run(
                ["python3", str(gate_script), "--skill", str(skill_dir)],
                capture_output=True, text=True, check=False, timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "timeout"
        if not proc.stdout.strip():
            return f"no-output (rc={proc.returncode})"
        try:
            return json.loads(proc.stdout).get("verdict", "unknown")
        except json.JSONDecodeError:
            return "unparseable"

    # Regenerated: look for scratch/assembled/<slug>/ — the unique subdir
    assembled_root = scratch / "assembled"
    regenerated = "n/a"
    if assembled_root.is_dir():
        children = [c for c in assembled_root.iterdir() if c.is_dir()]
        if len(children) == 1:
            regenerated = _run_gate(children[0])
        elif len(children) > 1:
            regenerated = f"ambiguous ({len(children)} assembled dirs)"

    committed_v = _run_gate(committed)

    if regenerated == "n/a":
        match = committed_v == "pass"
    else:
        match = regenerated == "pass" and committed_v == "pass"

    return {
        "regenerated": regenerated,
        "committed": committed_v,
        "match": match,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: self_bootstrap_diff.py <scratch-dir> <committed-skill-dir>",
              file=sys.stderr)
        return 2

    scratch = Path(argv[1]).expanduser().resolve()
    committed = Path(argv[2]).expanduser().resolve()

    if not scratch.is_dir():
        print(f"error: scratch dir not found: {scratch}", file=sys.stderr)
        return 2
    if not committed.is_dir():
        print(f"error: committed skill dir not found: {committed}", file=sys.stderr)
        return 2

    fired = detect_fired_phases(scratch)
    artifacts = [check_artifact(scratch, p) for p in fired if p in _LINT_COMMANDS]
    sections = section_match(scratch, committed)
    gates = gate_verdicts(scratch, committed)

    # Stage 10c: expected fired phases for the self-bootstrap fixture.
    # Phase 8 (08-assemble-and-gate) is always-fires post-Stage-10b but
    # we tolerate its absence for backward compatibility with pre-10b runs.
    expected_phases_3 = {"03-skill-frontmatter", "04-skill-phase-designer", "05-skill-references-scaffolder"}
    expected_phase_8 = "08-assemble-and-gate"
    fired_set = set(fired)
    missing = sorted(expected_phases_3 - fired_set)
    extra = sorted(fired_set - expected_phases_3 - {expected_phase_8})
    all_lints_pass = all(
        isinstance(a.get("lint"), dict) and a["lint"].get("passed") is True
        for a in artifacts
    )

    if missing or not all_lints_pass:
        verdict = "divergence"
    elif extra:
        verdict = "divergence"  # extra phases fired (e.g., is_scheduled leaked)
    elif not gates.get("match"):
        # Stage 10c: gate-verdict-match invariant. Both runs must PASS for
        # a clean self-bootstrap. Pre-10b runs (regenerated="n/a") fall
        # through cleanly when committed is "pass".
        verdict = "divergence"
    else:
        verdict = "pass"

    report = {
        "fired_phases": fired,
        "expected_phases": sorted(expected_phases_3 | {expected_phase_8}),
        "missing_phases": missing,
        "extra_phases": extra,
        "artifacts": artifacts,
        "section_match": sections,
        "gate_verdicts": gates,
        "verdict": verdict,
    }
    print(json.dumps(report, indent=2))
    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
