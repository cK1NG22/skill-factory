#!/usr/bin/env python3
"""
Skill compliance checker — validates Claude Code skills against the compliance checklist.
Pure stdlib, no external dependencies. Outputs structured JSON to stdout.
"""

import sys
import os
import re
import json
from pathlib import Path

ALLOWED_KEYS = {
    "name", "description", "license", "allowed-tools", "metadata",
    "compatibility", "model", "context", "user-invocable",
    "disable-model-invocation", "argument-hint",
}
GSTACK_KEYS = {"preamble-tier", "version", "benefits-from"}
TRIGGER_PATTERNS = re.compile(
    r"use when|trigger when|trigger phrases|use this skill when|trigger:",
    re.IGNORECASE,
)


def parse_frontmatter(content):
    """Parse YAML frontmatter between --- markers. Returns (dict, body_text) or (None, content)."""
    if not content.startswith("---"):
        return None, content
    # Find the closing ---
    end = content.find("\n---", 3)
    if end == -1:
        return None, content
    raw = content[4:end]
    body = content[end + 4:]  # after closing ---\n

    fm = {}
    current_key = None
    current_value_lines = []
    is_multiline = False
    is_list = False

    def flush():
        nonlocal current_key, current_value_lines, is_multiline, is_list
        if current_key is None:
            return
        if is_list:
            fm[current_key] = [line.strip().lstrip("- ") for line in current_value_lines if line.strip()]
        elif is_multiline:
            fm[current_key] = " ".join(line.strip() for line in current_value_lines if line.strip())
        else:
            fm[current_key] = current_value_lines[0] if current_value_lines else ""
        current_key = None
        current_value_lines = []
        is_multiline = False
        is_list = False

    for line in raw.split("\n"):
        # Top-level key: value
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*(.*)", line)
        if m:
            flush()
            key = m.group(1).strip()
            value = m.group(2).strip()
            current_key = key
            if value in (">", "|", ""):
                is_multiline = True
                current_value_lines = []
            elif value.startswith("["):
                # Inline list like [a, b, c]
                items = value.strip("[]").split(",")
                fm[key] = [i.strip().strip("'\"") for i in items if i.strip()]
                current_key = None
            else:
                current_value_lines = [value]
            continue

        # Continuation line (indented)
        if current_key and line.startswith(("  ", "\t")):
            stripped = line.strip()
            if stripped.startswith("- "):
                is_list = True
                current_value_lines.append(stripped)
            else:
                current_value_lines.append(stripped)
            continue

        # Non-indented, non-key line — flush
        if current_key:
            flush()

    flush()
    return fm, body


def count_lines(text):
    """Count non-empty lines in text."""
    return len(text.strip().split("\n")) if text.strip() else 0


def check_skill(skill_path):
    """Run all 13 compliance checks on a skill directory. Returns result dict."""
    skill_path = Path(skill_path)
    checks = []
    skill_name_found = None

    # --- Check 1: SKILL.md exists ---
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        checks.append({
            "id": 1, "name": "skill_md_exists", "severity": "required",
            "status": "fail", "message": "SKILL.md not found",
        })
        return {
            "skill_path": str(skill_path),
            "skill_name": skill_path.name,
            "checks": checks,
            "summary": {"passed": 0, "warnings": 0, "failures": 1, "total": 1},
        }

    checks.append({
        "id": 1, "name": "skill_md_exists", "severity": "required",
        "status": "pass", "message": "SKILL.md exists",
    })

    content = skill_md.read_text()
    fm, body = parse_frontmatter(content)

    if fm is None:
        checks.append({
            "id": 2, "name": "name_exists", "severity": "required",
            "status": "fail", "message": "No valid YAML frontmatter found",
        })
        return {
            "skill_path": str(skill_path),
            "skill_name": skill_path.name,
            "checks": checks,
            "summary": {"passed": 1, "warnings": 0, "failures": 1, "total": 2},
        }

    # --- Check 2: name field exists ---
    name = fm.get("name", "")
    if isinstance(name, list):
        name = name[0] if name else ""
    name = str(name).strip()
    if not name:
        checks.append({
            "id": 2, "name": "name_exists", "severity": "required",
            "status": "fail", "message": "Missing 'name' field in frontmatter",
        })
    else:
        skill_name_found = name
        checks.append({
            "id": 2, "name": "name_exists", "severity": "required",
            "status": "pass", "message": f"name: '{name}'",
        })

    # --- Check 3: name format valid ---
    if name:
        issues = []
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", name):
            issues.append("must be kebab-case (lowercase, digits, hyphens)")
        if "--" in name:
            issues.append("contains consecutive hyphens")
        if len(name) > 64:
            issues.append(f"too long ({len(name)} chars, max 64)")
        if issues:
            checks.append({
                "id": 3, "name": "name_format", "severity": "required",
                "status": "fail", "message": f"name '{name}': {'; '.join(issues)}",
            })
        else:
            checks.append({
                "id": 3, "name": "name_format", "severity": "required",
                "status": "pass", "message": f"name '{name}' is valid kebab-case, {len(name)} chars",
            })
    else:
        checks.append({
            "id": 3, "name": "name_format", "severity": "required",
            "status": "fail", "message": "Cannot validate format — name is missing",
        })

    # --- Check 4: description field exists ---
    desc = fm.get("description", "")
    if isinstance(desc, list):
        desc = " ".join(str(d) for d in desc)
    desc = str(desc).strip()
    if not desc:
        checks.append({
            "id": 4, "name": "description_exists", "severity": "required",
            "status": "fail", "message": "Missing 'description' field in frontmatter",
        })
    else:
        checks.append({
            "id": 4, "name": "description_exists", "severity": "required",
            "status": "pass", "message": f"description present ({len(desc)} chars)",
        })

    # --- Check 5: description ≤1024 chars ---
    if desc:
        if len(desc) > 1024:
            checks.append({
                "id": 5, "name": "description_length", "severity": "required",
                "status": "fail", "message": f"description is {len(desc)} chars (max 1024)",
            })
        else:
            checks.append({
                "id": 5, "name": "description_length", "severity": "required",
                "status": "pass", "message": f"description is {len(desc)} chars (max 1024)",
            })
    else:
        checks.append({
            "id": 5, "name": "description_length", "severity": "required",
            "status": "pass", "message": "No description to check length on (already flagged)",
        })

    # --- Check 6: no unexpected frontmatter keys ---
    unexpected = set(fm.keys()) - ALLOWED_KEYS - GSTACK_KEYS
    gstack_found = set(fm.keys()) & GSTACK_KEYS
    if unexpected:
        checks.append({
            "id": 6, "name": "frontmatter_keys", "severity": "required",
            "status": "fail", "message": f"Unexpected keys: {', '.join(sorted(unexpected))}",
        })
    elif gstack_found:
        checks.append({
            "id": 6, "name": "frontmatter_keys", "severity": "info",
            "status": "info", "message": f"gstack keys present (tolerated): {', '.join(sorted(gstack_found))}",
        })
    else:
        checks.append({
            "id": 6, "name": "frontmatter_keys", "severity": "required",
            "status": "pass", "message": "All frontmatter keys are recognized",
        })

    # --- Check 7: description has trigger phrases ---
    if desc:
        if TRIGGER_PATTERNS.search(desc):
            checks.append({
                "id": 7, "name": "trigger_phrases", "severity": "best-practice",
                "status": "pass", "message": "Description contains trigger phrases",
            })
        else:
            checks.append({
                "id": 7, "name": "trigger_phrases", "severity": "best-practice",
                "status": "warn", "message": "Description lacks trigger phrases (no 'Use when', 'Trigger when', etc.)",
            })
    else:
        checks.append({
            "id": 7, "name": "trigger_phrases", "severity": "best-practice",
            "status": "warn", "message": "No description to check for trigger phrases",
        })

    # --- Check 8: description > 100 chars ---
    if desc:
        if len(desc) > 100:
            checks.append({
                "id": 8, "name": "description_pushy", "severity": "best-practice",
                "status": "pass", "message": f"Description is {len(desc)} chars (>100 threshold)",
            })
        else:
            checks.append({
                "id": 8, "name": "description_pushy", "severity": "best-practice",
                "status": "warn", "message": f"Description is only {len(desc)} chars — may undertrigger (aim for >100)",
            })
    else:
        checks.append({
            "id": 8, "name": "description_pushy", "severity": "best-practice",
            "status": "warn", "message": "No description present",
        })

    # --- Check 9: body ≤500 lines ---
    body_lines = count_lines(body)
    if body_lines > 500:
        checks.append({
            "id": 9, "name": "body_max_lines", "severity": "best-practice",
            "status": "warn", "message": f"Body is {body_lines} lines (max 500)",
        })
    else:
        checks.append({
            "id": 9, "name": "body_max_lines", "severity": "best-practice",
            "status": "pass", "message": f"Body is {body_lines} lines (max 500)",
        })

    # --- Check 10: body in 180-220 range (info only) ---
    if 180 <= body_lines <= 220:
        checks.append({
            "id": 10, "name": "body_ideal_range", "severity": "info",
            "status": "pass", "message": f"Body is {body_lines} lines (ideal 180-220 range)",
        })
    else:
        checks.append({
            "id": 10, "name": "body_ideal_range", "severity": "info",
            "status": "info", "message": f"Body is {body_lines} lines (ideal range is 180-220)",
        })

    # --- Check 11: references/ exists if body > 300 lines ---
    refs_dir = skill_path / "references"
    if body_lines > 300:
        if refs_dir.is_dir():
            checks.append({
                "id": 11, "name": "references_for_large", "severity": "best-practice",
                "status": "pass", "message": f"Body is {body_lines} lines and references/ exists",
            })
        else:
            checks.append({
                "id": 11, "name": "references_for_large", "severity": "best-practice",
                "status": "warn", "message": f"Body is {body_lines} lines but no references/ directory — consider extracting content",
            })
    else:
        checks.append({
            "id": 11, "name": "references_for_large", "severity": "best-practice",
            "status": "pass", "message": f"Body is {body_lines} lines — no references/ needed",
        })

    # --- Check 12: references one level deep ---
    if refs_dir.is_dir():
        nested = [d for d in refs_dir.iterdir() if d.is_dir()]
        if nested:
            checks.append({
                "id": 12, "name": "references_depth", "severity": "best-practice",
                "status": "warn", "message": f"references/ has nested subdirectories: {', '.join(d.name for d in nested)}",
            })
        else:
            checks.append({
                "id": 12, "name": "references_depth", "severity": "best-practice",
                "status": "pass", "message": "references/ is one level deep",
            })
    else:
        checks.append({
            "id": 12, "name": "references_depth", "severity": "best-practice",
            "status": "pass", "message": "No references/ directory (check not applicable)",
        })

    # --- Check 13: steps reference knowledge sources ---
    if refs_dir.is_dir() and body_lines > 200:
        step_pattern = re.compile(r"^\d+\.|^##.*(?:Step|Phase)", re.MULTILINE)
        ref_pattern = re.compile(r"references/", re.IGNORECASE)
        steps = len(step_pattern.findall(body))
        refs = len(ref_pattern.findall(body))
        if steps > 0:
            ratio = refs / steps
            if ratio < 0.3:
                checks.append({
                    "id": 13, "name": "step_knowledge_refs", "severity": "best-practice",
                    "status": "warn",
                    "message": f"{refs} reference mentions across {steps} steps ({ratio:.0%}) — aim for >30%",
                })
            else:
                checks.append({
                    "id": 13, "name": "step_knowledge_refs", "severity": "best-practice",
                    "status": "pass",
                    "message": f"{refs} reference mentions across {steps} steps ({ratio:.0%})",
                })
        else:
            checks.append({
                "id": 13, "name": "step_knowledge_refs", "severity": "best-practice",
                "status": "pass", "message": "No numbered steps detected (check not applicable)",
            })
    else:
        checks.append({
            "id": 13, "name": "step_knowledge_refs", "severity": "best-practice",
            "status": "pass", "message": "Check not applicable (no references/ or body ≤200 lines)",
        })

    # Build summary
    passed = sum(1 for c in checks if c["status"] == "pass")
    warnings = sum(1 for c in checks if c["status"] == "warn")
    failures = sum(1 for c in checks if c["status"] == "fail")

    return {
        "skill_path": str(skill_path),
        "skill_name": skill_name_found or skill_path.name,
        "checks": checks,
        "summary": {
            "passed": passed,
            "warnings": warnings,
            "failures": failures,
            "total": len(checks),
        },
    }


def is_gstack_skill(skill_path):
    """Detect gstack skills by frontmatter markers or description tag."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False
    try:
        # Read just the frontmatter portion for speed
        content = skill_md.read_text()
        head = content[:2000]
        # Check for gstack-specific frontmatter keys
        if re.search(r"^preamble-tier:", head, re.MULTILINE):
            return True
        if re.search(r"^version:", head, re.MULTILINE):
            return True
        # Check for (gstack) tag in description
        if "(gstack)" in head:
            return True
    except Exception:
        pass
    return False


def find_skills(include_archived=False):
    """Find all non-gstack, non-symlinked skill directories under ~/.claude/skills/."""
    skills_dir = Path.home() / ".claude" / "skills"
    results = []
    skipped = 0
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("_") and not include_archived:
            continue
        if entry.is_symlink():
            skipped += 1
            continue
        if is_gstack_skill(entry):
            skipped += 1
            continue
        results.append(entry)
    return results, skipped


def main():
    args = sys.argv[1:]
    include_archived = "--include-archived" in args
    args = [a for a in args if not a.startswith("--")]
    scan_all = "--all" in sys.argv[1:]

    if scan_all:
        skills, skipped = find_skills(include_archived)
    elif args:
        skills = [Path(a) for a in args]
        skipped = 0
    else:
        print("Usage: compliance_check.py [--all] [path1 path2 ...] [--include-archived]", file=sys.stderr)
        sys.exit(1)

    results = [check_skill(s) for s in skills]

    output = {
        "results": results,
        "skipped_symlinks": skipped if scan_all else 0,
        "total_skills_checked": len(results),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
