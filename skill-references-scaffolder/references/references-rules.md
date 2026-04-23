# References-scaffolder rules — authoritative contract

Three rules govern how a factory-authored skill's `references/` folder is structured and cited. Rule A is universal whenever a `references/` folder exists. Rule B is conditional on `has_references`. Rule C is conditional on `has_phases`.

The deterministic lint at `scripts/references_lint.py` checks each rule mechanically. When this document and the lint script diverge, **the lint is authoritative** — update this document to match the lint, not the other way around (factory convention per the `skill-frontmatter` and `skill-phase-designer` precedents).

---

## Rule A — `references/` is one level deep (BP-008, universal)

When a skill's root contains a `references/` directory, every child must be a file. No sub-directories. No symlinks that resolve to directories.

**Why:** Nested reference chains (`references/phase-1/scoping/questions.md`) defeat on-demand loading — the agent cannot skim a flat index to decide which file to read. The whole point of `references/` is a lazy-load registry, and a registry whose entries are themselves folders is no longer a registry.

**Correct:**
```
skill-foo/
  references/
    scoping-questions.md
    strategy-overview.md
    anti-patterns.md
```

**Incorrect:**
```
skill-foo/
  references/
    phase-1/
      scoping/
        questions.md
```

**Lint behaviour:** if `references/` exists and contains any sub-directory (including a symlinked directory), the lint fails with the list of offending sub-paths. If `references/` does not exist, this rule is silent — Rule A has nothing to enforce.

---

## Rule B — SKILL.md cites each reference file (BP-007, only if `has_references`)

When the `has_references` trait fires, every `.md` file directly under `references/` must be cited at least once in SKILL.md. The canonical citation form is:

> Read `references/<name>.md` for <purpose>.

Accepted verbs (case-insensitive): `Read`, `See`, `Consult`, `Load`, `Use`, `Refer to`, `per`.

**Why:** A reference file that SKILL.md never names is unreachable — the agent has no trigger to open it. BP-007's whole promise (detail available, not always loaded) assumes the SKILL.md body contains the explicit "open this file for that reason" instruction.

**Correct:**
```markdown
### Step 3 — Ask scoping questions

Read `references/scoping-questions.md` for the full list. Ask only the first four
inline.
```

**Non-canonical but tolerated (warn, not fail):**
```markdown
The anti-patterns live in references/anti-patterns.md.
```
(No canonical verb — the agent may still find it, but the phrasing is weaker. Lint emits a `warns` entry.)

**Incorrect:**
```
references/
  anti-patterns.md   ← file exists
```
SKILL.md never names `anti-patterns.md`. Lint fails with the uncited-file list.

### Inline-content sub-rule — long inline blocks must be moved

The same rule also fails when SKILL.md itself contains a content block that *should* live in a reference file:

- **Tables:** >= 10 consecutive pipe-delimited rows anywhere in SKILL.md.
- **Dense prose / lists:** >= 20 consecutive non-blank, non-heading lines with no section break.

Both signal that the SKILL.md is carrying content that belongs in `references/<topic>.md`. Fenced code blocks are excluded — example shell/markdown snippets do not trigger this check.

**Fix:** move the block to `references/<topic>.md`, replace with a single-line citation.

---

## Rule C — Parallel folders at the same depth (BP-009, only if `has_phases`)

When `has_phases` fires, the skill root must expose `phases/` and `references/` as siblings. Nesting one inside the other is a structural violation:

- `phases/<name>/references/` — a phase-local references folder — fails.
- `references/<name>/phases/` — a reference-local phases folder — fails.

`assets/` is a third optional sibling. Its absence emits a `warns` entry, not a fail — many skills have no templates or static files.

**Correct:**
```
skill-foo/
  SKILL.md
  phases/
  references/
  assets/        ← optional
```

**Incorrect:**
```
skill-foo/
  phases/
    phase-1/
      references/       ← nested; Rule C fail
        foo.md
```

**Why:** Two parallel sibling folders at the same depth is clean and lazy-load-friendly. Nesting a knowledge folder inside a process folder (or vice versa) couples them in a way that breaks BP-008 and makes on-demand loading opaque.

**Lint behaviour:**
- Missing `phases/` when `--has-phases` is set → fail.
- Missing `references/` when `--has-phases` is set → fail (parallel-folder pattern requires both).
- Any `phases/*/references/` or `references/*/phases/` → fail.
- Missing `assets/` → warn (optional).

---

## Composed worked example — acme-strategy-coach

```
skill-acme-strategy-coach/
  SKILL.md                             ← cites all four reference files
  phases/
    01-intake/
      input.md
    02-diagnose/
      input.md
  references/
    scoping-questions.md
    strategy-overview.md
    frameworks-map.md
    anti-patterns.md
  assets/
    report-template.docx
```

Traits: `has_phases: true`, `has_references: true`. Lint invocation:

```bash
python3 scripts/references_lint.py skill-acme-strategy-coach/ \
  --has-references --has-phases
```

Verdict: `passed: true`, 0 fails, 0 warns.
