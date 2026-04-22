---
name: skill-compliance
description: >
  Audit skills against the compliance checklist — frontmatter validation,
  best practices, structural health. Use when: "audit skills", "check skill
  compliance", "validate my skills", "skill health check", "are my skills
  compliant", "run compliance", "check all skills". Also trigger when the
  user asks about skill quality or mentions the compliance checklist.
argument-hint: "[skill name, path, or 'all']"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# Skill Compliance Checker

Audit skills against 13 compliance checks: 6 required (FAIL if broken) and 7 best-practice (WARN).
This skill is report-only — flag what failed and why. Do not auto-fix anything.

---

## Phase 0: Resolve Targets

Determine which skill(s) to check based on user input.

**If the user provided a skill name** (e.g., "brain-dump"):
- Resolve to `~/.claude/skills/<name>/`
- If that path doesn't exist, check if they gave a full path

**If the user said "all":**
- The script handles this with `--all`
- Symlinked skills (gstack-managed) are skipped automatically
- `_archived/` is skipped by default

**If no input or ambiguous:**
- Use AskUserQuestion to present the list of installed skills plus an "all" option
- To get the list, run: `ls -1 ~/.claude/skills/ | grep -v '^_'`

---

## Phase 1: Run Compliance Script

Run the checker script. The script path is relative to this skill's directory.

### Single skill:
```
python3 <this_skill_dir>/scripts/compliance_check.py <skill_path>
```

### All skills:
```
python3 <this_skill_dir>/scripts/compliance_check.py --all
```

The script outputs JSON to stdout. Parse it for Phase 2.

If the script errors (non-JSON output), show the raw error to the user.

---

## Phase 2: Present Results

Read the JSON output and present results to the user.

### For a single skill:

Show all 13 checks in order:

```
## <skill-name>

PASS  name: 'brain-dump'
PASS  name is valid kebab-case, 10 chars
FAIL  Missing 'description' field in frontmatter
WARN  Body is 347 lines (max 500)
INFO  Body is 347 lines (ideal range is 180-220)
...

Result: 10 passed, 2 warnings, 1 failure
```

Use these indicators:
- `PASS` — check passed
- `FAIL` — required check failed
- `WARN` — best practice not met
- `INFO` — advisory information (not a problem)

### For all skills:

**First**, show a summary table — one row per skill, only columns for name, passed, warnings, failures:

```
| Skill             | Pass | Warn | Fail |
|-------------------|------|------|------|
| brain-dump        | 13   | 0    | 0    |
| api-design        | 8    | 1    | 2    |
| ...               |      |      |      |
```

Note how many gstack skills were skipped (from `skipped_symlinks` in JSON).

**Then**, show expanded details ONLY for skills with failures or warnings.
Skills that are fully clean get no expanded section — the summary row is enough.

### End with totals:
```
Checked X skills (Y gstack skills skipped).
Overall: A passed, B warnings, C failures across all skills.
```

---

## Phase 3: Done

Do NOT suggest fixes or next steps. The user will use the report as input to refine skills themselves.

If the user asks about a specific check or wants more detail, explain what that check looks for and why it matters — but do not propose code changes.

---

## Check Reference

The script runs 13 checks in two tiers:

### Required (FAIL)
1. SKILL.md exists
2. `name` field exists in frontmatter
3. `name` is kebab-case, ≤64 chars, no consecutive hyphens
4. `description` field exists in frontmatter
5. `description` is ≤1024 chars
6. No unexpected frontmatter keys

### Best Practice (WARN)
7. Description contains trigger phrases ("Use when", "Trigger when", etc.)
8. Description is >100 chars (proxy for "pushy enough" to trigger reliably)
9. Body is ≤500 lines
10. Body is in 180-220 line ideal range (INFO only, not a warning)
11. `references/` directory exists if body exceeds 300 lines
12. Reference files are one level deep (no nested subdirectories)
13. Steps reference knowledge sources (≥30% of numbered steps mention a reference file)

### gstack keys
Keys like `preamble-tier`, `version`, `benefits-from` are tolerated with INFO status.
They are not failures — they're gstack-specific extensions to the frontmatter spec.
