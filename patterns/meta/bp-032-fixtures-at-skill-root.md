# BP-032: Fixtures live at the skill root as `fixtures/`, not under `references/`

**Source:** Stage 3 of skill-factory build (2026-04-22); surfaced by `/skill-compliance` flagging `references/fixtures/` as a nested-reference violation.
**Category:** Authoring discipline (Meta — factory sub-skill layout)

**Why:** `references/fixtures/` appears nested under `references/`, which triggers the BP-008 "one level deep" compliance warning. Fixtures are test data (not reference content the skill loads during live invocations), so they belong parallel to `references/`, following the BP-009 pattern. This keeps `references/` flat and the compliance check clean.

**When applicable:** Every factory sub-skill that ships with fixtures (all of them, per BP-029 "no sub-skill ships without fixtures"). Factory-internal convention; not applied to client skills.

**Enforced by:** `skill-references-scaffolder` (will refuse to nest `fixtures/` under `references/`); `skill-compliance` (BP-008 catches the misplacement).

**Correct layout:**
```
skill-X/
├── SKILL.md
├── references/
│   └── <rule-contracts>.md
└── fixtures/
    ├── passing-input.md
    ├── gaps-input.md (or failing-input.md)
    ├── expected-pass.md
    └── expected-gaps.md
```

**Incorrect layout:**
```
skill-X/
├── SKILL.md
└── references/
    ├── <rule-contracts>.md
    └── fixtures/        ← triggers BP-008 warning
        └── ...
```

**Naming convention:** At minimum, one passing fixture + one failing fixture + an `expected-*.md` per fixture showing the exact output the skill must produce. Additional fixtures named after the scenario they exercise (e.g., `fixtures/large-input.md` + `fixtures/expected-large.md`).
