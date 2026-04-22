# PATTERNS — best-practices catalog

The single source of truth for every authoring discipline `skill-factory` enforces. Every sub-skill points back to one or more `BP-###` entries here. Patterns are added BEFORE the code that enforces them.

**Discipline:**
- New pattern → PR adding a `BP-###` entry → only then PR adding the sub-skill change that enforces it.
- A pattern that no sub-skill enforces is either a TODO (mark `**Enforced by:** none yet`) or removed.
- Each entry must answer: *what is the rule, why does it exist, when does it apply, who enforces it, what's correct vs incorrect.*

---

## Frontmatter & description

### BP-001: Description must include explicit trigger phrases
**Source:** Anthropic skill-creator + `tooling-skill-writing-patterns.md`
**Why:** Claude undertriggers skills when descriptions lack literal trigger phrases. Description is the only signal the dispatcher uses to decide whether the skill applies. Past incident: 411-refine wouldn't fire on "use after research" because Claude expected "use when".
**When applicable:** Every archetype.
**Enforced by:** `skill-frontmatter`, `skill-description-triggers`
**Correct:** `"Convert markdown to docx. Use when 'convert markdown to docx', 'md to word doc', 'turn this md into word'."`
**Incorrect:** `"Generates documents."`

### BP-002: Description must be slightly "pushy"
**Source:** Anthropic skill-creator (line 67)
**Why:** Claude's default behavior is to NOT consult skills for tasks it thinks it can handle directly. "Pushy" means listing concrete trigger phrases, naming the skill explicitly in those triggers, and making the use-cases unambiguous. Soft descriptions get skipped.
**When applicable:** Every archetype.
**Enforced by:** `skill-frontmatter`, `skill-description-triggers`
**Correct:** Lists 5–10 verbatim trigger phrases in quotes; names file types, tools, or domains.
**Incorrect:** Generic verbs without context ("creates a document", "generates a report").

### BP-003: Name is ≤64 chars, lowercase + hyphens + numbers only
**Source:** Anthropic skill-creator compliance checklist
**Why:** Hard runtime limit. Names with spaces, uppercase, or special chars cause invocation errors. Reserved words ("anthropic", "claude") are blocked.
**When applicable:** Every archetype.
**Enforced by:** `skill-frontmatter`, `skill-compliance`
**Correct:** `acme-onboarding`, `411-deck`, `skill-spec-validator`
**Incorrect:** `Acme_Onboarding`, `claude-helper`, `My Skill`

### BP-004: Description ≤1024 chars
**Source:** Anthropic skill-creator compliance checklist
**Why:** Descriptions get truncated past 1024 chars; trigger phrases at the end are silently dropped, breaking discoverability.
**When applicable:** Every archetype.
**Enforced by:** `skill-frontmatter`, `skill-compliance`
**Correct:** ~600–900 chars including 5–10 trigger phrases and a "Do NOT use for…" negative-case clause.
**Incorrect:** A 1500-char essay describing the skill's history and rationale.

### BP-005: `allowed-tools` declared in frontmatter
**Source:** `tooling-skill-writing-patterns.md`
**Why:** Without `allowed-tools`, every tool use mid-skill triggers a permission prompt — disruptive and breaks long workflows. Pre-declaring authorizes the tools at skill load.
**When applicable:** Every archetype, especially HITL/pipeline that span many tool calls.
**Enforced by:** `skill-frontmatter`, `skill-compliance`
**Correct:** `allowed-tools: [AskUserQuestion, Agent, Read, Write, Bash, WebFetch]`
**Incorrect:** Frontmatter omits `allowed-tools`; user gets prompts mid-flow.

---

## File structure & references

### BP-006: SKILL.md is a traffic director, 180–220 lines
**Source:** `tooling-skill-writing-patterns.md` (research-confirmed 2026-03-03)
**Why:** Lazy-loading benefit lost if SKILL.md balloons. Detail belongs in `references/`. Adding new content should never increase SKILL.md — it goes to references/. The Anthropic 500-line ceiling is the absolute max; 180–220 is the working target.
**When applicable:** Phased HITL, pipeline-orchestrator, research/synthesis, multi-model-reasoning, taste-gated HITL, meta/optimizer, guidance/consult.
**Enforced by:** `skill-references-scaffolder`, `skill-compliance`
**Correct:** SKILL.md has 6 phases × ~25 lines each + frontmatter; detailed rubrics in `references/`.
**Incorrect:** SKILL.md is 600 lines because the author inlined rubrics, examples, and lookup tables.

### BP-007: Detail in `references/`, loaded on demand
**Source:** Anthropic skill-creator + `tooling-skill-writing-patterns.md`
**Why:** Reference files only load into context when SKILL.md explicitly says "Read references/X.md for [purpose]." This keeps context lean — detail available, not always loaded.
**When applicable:** Any archetype with frameworks, lookup tables, or examples > ~10 lines.
**Enforced by:** `skill-references-scaffolder`, `skill-compliance`
**Correct:** SKILL.md says `Read references/strategy-overview.md to load the per-phase theory map.`
**Incorrect:** SKILL.md inlines a 200-line table of frameworks.

### BP-008: References are one level deep — no nested chains
**Source:** Anthropic skill-creator compliance checklist
**Why:** `references/foo/bar/baz.md` defeats lazy-loading and makes navigation opaque. Compliance check fails on nesting.
**When applicable:** Every archetype.
**Enforced by:** `skill-references-scaffolder`, `skill-compliance`
**Correct:** `references/scoping-questions.md`, `references/strategy-overview.md`, `references/anti-patterns.md`
**Incorrect:** `references/phase-1/scoping/questions.md`

### BP-009: Parallel folders for complex skills (`phases/` + `references/` + `assets/`)
**Source:** `tooling-skill-writing-patterns.md`; confirmed in 411-case (7 phases, 12 references, 3 assets)
**Why:** When a skill has both process instructions (phase files) and knowledge content (theory/framework files), separate them into parallel top-level folders. Two parallel folders at the same depth is fine and does not violate the one-level rule. Nesting `references/` inside `phases/` IS a violation.
**When applicable:** Phased HITL, pipeline-orchestrator, multi-model-reasoning, research/synthesis with 3+ phases.
**Enforced by:** `skill-references-scaffolder`
**Correct:** `skill-name/{SKILL.md, phases/, references/, assets/}` all at one depth.
**Incorrect:** `phases/phase-1/references/foo.md` — nested.

### BP-010: Apply once, carry forward, reference later
**Source:** `tooling-skill-writing-patterns.md`; emerged from 411-case build
**Why:** Each reference file should be read at the FIRST phase where its knowledge is needed. The phase's output carries the insight forward. Later phases reference *the output*, not the original file. Eliminates redundant reads, keeps each phase focused.
**When applicable:** Phased HITL, pipeline-orchestrator, research/synthesis.
**Enforced by:** `skill-phase-designer`
**Correct:** Phase 1 reads `references/strategy-overview.md`, writes its synthesis to `phase-1-output.md`. Phase 4 reads `phase-1-output.md`, not strategy-overview again.
**Incorrect:** Every phase opens with "Re-read references/strategy-overview.md."

---

## Workflow & human-in-the-loop

### BP-011: Announce phase transitions
**Source:** `tooling-skill-writing-patterns.md`
**Why:** In long workflows, users lose track of where they are. Explicit phase announcements keep them oriented and provide natural review checkpoints.
**When applicable:** Phased HITL, taste-gated HITL, pipeline-orchestrator, research/synthesis, guidance/consult.
**Enforced by:** `skill-phase-designer`
**Correct:** `Announce: "Starting Phase 2: Solution Development. We'll generate 3–5 candidate solutions before committing to one."`
**Incorrect:** Skill silently transitions between phases; user can't tell what changed.

### BP-012: Hard gates ("Do NOT proceed until…")
**Source:** `tooling-skill-writing-patterns.md`
**Why:** After every checkpoint where skipping ahead would be costly, an explicit gate prevents premature progression. Especially important in long workflows.
**When applicable:** Phased HITL, taste-gated HITL, pipeline-orchestrator. Density scales with reversibility — high-stakes steps need more gates.
**Enforced by:** `skill-phase-designer`
**Correct:** `Do NOT proceed to Phase 3 until the user confirms the chosen solution from Phase 2.`
**Incorrect:** No gate; skill barrels forward through expensive operations.

### BP-013: Ask user first, then suggest (never present-then-rubber-stamp)
**Source:** `tooling-skill-writing-patterns.md`
**Why:** Presenting a finished analysis and asking "looks good?" produces low-quality engagement. Asking the user what they think first, then layering Claude's analysis, produces actual collaboration.
**When applicable:** Phased HITL, taste-gated HITL, guidance/consult.
**Enforced by:** `skill-phase-designer`
**Correct:** Phase 1: "What do YOU think the root problem is?" → wait → "Here's how that compares to common framings…"
**Incorrect:** Phase 1: "Here's the problem analysis I generated. Approve?"

### BP-014: Add rationale with "because" — explain WHY
**Source:** `tooling-skill-writing-patterns.md`; reinforced in Anthropic skill-creator (lines 318-321)
**Why:** LLMs follow reasoning better than directives. Rationale also helps handle edge cases the skill description doesn't cover. ALL-CAPS MUSTs without rationale are a yellow flag.
**When applicable:** Every archetype, especially anywhere the skill imposes a non-obvious constraint.
**Enforced by:** all sub-skills (review for "because" clauses)
**Correct:** `Generate 3–5 candidate solutions — because exhausting the solution space before committing prevents anchoring on the first good idea.`
**Incorrect:** `Generate 3–5 candidate solutions. ALWAYS.`

### BP-015: Number all questions, use `AskUserQuestion` for choices
**Source:** `tooling-skill-writing-patterns.md`
**Why:** Numbered questions get answered in full; unnumbered prompts get partial responses. `AskUserQuestion` (vs plain text) is the right tool for choices because it provides structured options instead of free-text guessing.
**When applicable:** Phased HITL, taste-gated HITL, guidance/consult.
**Enforced by:** `skill-phase-designer`
**Correct:** `Answer all four before proceeding: 1. … 2. … 3. … 4. …` Or `AskUserQuestion(...)` with explicit options.
**Incorrect:** "Tell me about X, Y, and Z" — usually returns just X.

### BP-016: Inline question rule — ≤4 questions, each one short sentence
**Source:** `tooling-skill-writing-patterns.md`
**Why:** Question lists in SKILL.md add to context cost. Beyond 4 short questions, move to a `references/scoping-questions.md` and call it from SKILL.md. Keeps the traffic-director lean.
**When applicable:** Phased HITL, guidance/consult.
**Enforced by:** `skill-phase-designer`, `skill-references-scaffolder`
**Correct:** Inline: 4 single-sentence questions. Or: "Ask the questions in `references/scoping-questions.md`."
**Incorrect:** SKILL.md inlines 12 questions with multi-sentence explanations.

---

## KPIs & evaluation

### BP-017: KPIs are Observable, Specific, Not gameable, Not compound
**Source:** `feedback-kpi-stress-test.md`; emerged from `/kpi-setter` testing
**Why:** Vague KPIs ("self-contained", "complexity matches") can't be reliably evaluated by a grader. Each KPI must be checkable from the output alone (Observable), point at a concrete artifact (Specific), resist surface-compliance hacks (Not gameable), and test ONE thing (Not compound).
**When applicable:** Any archetype that wants `/autoresearch` refinement (phased HITL, pipeline-orchestrator, research/synthesis, meta/optimizer).
**Enforced by:** `skill-kpi-design` (auto-runs the stress-test before presenting KPIs).
**Correct:** `KPI: output.yaml contains a "trigger_phrases" key with ≥5 string entries.`
**Incorrect:** `KPI: trigger phrases are good.`

### BP-018: KPI before autoresearch — never run autoresearch without `kpi.md`
**Source:** `hub-skills-tooling.md` rules
**Why:** `/autoresearch` grades against `kpi.md`. Without one, the optimizer has no gradient and produces garbage edits. The kpi.md must exist and pass stress-test BEFORE the optimization loop runs.
**When applicable:** Any archetype invoking `skill-autoresearch-gate`.
**Enforced by:** `skill-autoresearch-gate` (refuses to proceed without `kpi.md`).
**Correct:** Author runs `/skill-kpi-design` → produces `kpi.md` → then `/autoresearch <skill>`.
**Incorrect:** Author runs `/autoresearch <skill>` with no kpi.md; loop produces noise.

### BP-019: Eval test cases are realistic, substantive, and cover near-miss negatives
**Source:** Anthropic skill-creator description optimization (lines 360–376)
**Why:** Simple queries ("read this PDF") don't trigger skills regardless of description quality. Near-miss negatives (queries that share keywords with should-trigger but actually need something different) are the hardest test and the most discriminating.
**When applicable:** Any archetype invoking `skill-eval-loop` or `skill-description-triggers`.
**Enforced by:** `skill-description-triggers`
**Correct:** Realistic prompts with file paths, casual tone, edge cases. 8–10 should-trigger + 8–10 should-NOT-trigger near-misses.
**Incorrect:** "Format this data" as the should-trigger query and "Write a fibonacci function" as the should-not-trigger.

---

## Output & rendering

### BP-020: Write the output contract FIRST (rendering contract)
**Source:** `feedback-deck-qa-checklist.md`; 411-refine refinement (baseline 0.572 → iter-1 0.827 on a single 8-line rendering-contract edit)
**Why:** When skills produce structured output, defining the output schema *before* the process steps eliminates ~40% of phase KPI misses. The contract forces inline rendering of all required sections, preventing "executive-summary-only" outputs that skip detail.
**When applicable:** Transformation, single-shot tool, review/audit, variant-generation, trend/longitudinal.
**Enforced by:** `skill-output-contract`
**Correct:** SKILL.md opens Section 5 with a `## Required output structure` block listing every section the output MUST contain.
**Incorrect:** Output format is implied by the process; the model produces a vague summary.

### BP-021: Outputs go to `~/Claude/<skill>/`, never `~/Desktop/` or project dirs
**Source:** `feedback-output-home-convention.md`
**Why:** `~/Desktop/` clutter is invisible-by-decay; project dirs pollute git status. `~/Claude/` is the single conventional output home with 30-day auto-archive.
**When applicable:** Transformation, single-shot tool, review/audit, research/synthesis, scheduled/cron.
**Enforced by:** `skill-output-contract`, `skill-compliance`
**Correct:** Output saved to `~/Claude/skill-factory/<session>/draft-skill/`.
**Incorrect:** Output saved to `~/Desktop/output.docx` or `./generated-stuff/`.

### BP-022: Cron/scheduled skills must expose: last-run, success, artifact location
**Source:** `feedback-automation-observability.md`
**Why:** Automated processes are invisible until they break. Every cron-archetype skill must answer three questions on demand: when did it last run, did it succeed, what did it produce. Without this, debugging requires log archaeology.
**When applicable:** Scheduled/cron, trend/longitudinal.
**Enforced by:** `skill-cron-observability`
**Correct:** Skill writes `~/Claude/<skill>/runs/<timestamp>/{result.json, artifact.X}` and a top-level `latest.json` symlink.
**Incorrect:** Cron skill emits to syslog only; user has no way to check status.

---

## Composition & pipelines

### BP-023: Sub-skill composition uses the `Agent` tool (not Read+inline)
**Source:** Phase 1 audit of `/skill-creator:189`, `/autoresearch:107`, `/dung`; rejected `context: fork` (zero live examples)
**Why:** `Agent` tool spawns subagents with isolated context — driver doesn't bloat with sub-skill intermediate work. Read+inline (used by `/locker`) shares context wastefully and conflates failure modes. Slash-command text in output does NOT trigger dispatch.
**When applicable:** Pipeline-orchestrator, multi-model-reasoning, the driver itself.
**Enforced by:** `skill-factory` driver, `skill-signed-handoff`
**Correct:** Driver lists `Agent` in `allowed-tools`; spawns sub-skill with prompt + skill path + workspace dir.
**Incorrect:** Driver `Read`s sub-skill SKILL.md and inlines the instructions.

### BP-024: Signed handoffs between pipeline skills (sha256 over argument-bearing fields)
**Source:** `411-deck-signed-handoff.md`; emerged from `/411-case → /411-deck` drift problem
**Why:** When skill A hands off content to skill B, B should be able to TRUST A's content without re-validating. Sha256 over argument-bearing fields (argument_flow, leadlines, callout_items, recommendation) lets B verify the contract was honored. Eliminates duplicate validation logic and drift.
**When applicable:** Pipeline-orchestrator, multi-model-reasoning, taste-gated HITL with multi-step handoff.
**Enforced by:** `skill-signed-handoff`
**Correct:** Upstream Phase 6 signs handoff via `scripts/deck_signature.py --sign`. Downstream Phase 1 verifies via `--verify`. Exit codes 0/1/2/3 surface specific failures.
**Incorrect:** Downstream re-validates argument structure from scratch; drift goes undetected.

### BP-025: Sub-skills are siblings (top-level), not nested under driver
**Source:** Phase 1 architecture decision
**Why:** Sibling sub-skills are independently invocable (`/skill-frontmatter` works alone), show in autocomplete, get their own autoresearch workspace, and have a single source of truth. Nesting under driver-skill loses all four.
**When applicable:** Every sub-skill in `skill-factory`.
**Enforced by:** `skill-references-scaffolder` (refuses to nest sub-skills)
**Correct:** `~/Projects/skill-factory/skill-frontmatter/SKILL.md` symlinked to `~/.claude/skills/skill-frontmatter`.
**Incorrect:** `~/Projects/skill-factory/skill-factory/sub-skills/frontmatter/SKILL.md` (nested, not invocable, not autocompleted).

---

## Hands-off operation

### BP-026: Sole human touchpoint = the input spec
**Source:** Carter's hands-off vision (skill-factory plan, Phase 4 round 2)
**Why:** The factory's quality ceiling is set by the input spec. Every mid-pipeline pause is a quality leak — the spec should have answered that question. Hands-off discipline forces every ambiguity back to the validator stage.
**When applicable:** The driver (`skill-factory`) and any pipeline-orchestrator built atop it.
**Enforced by:** `skill-factory` driver design — no `AskUserQuestion` calls past Phase 1.
**Correct:** Spec passes validator → factory runs end-to-end → produces 13/13-compliant skill.
**Incorrect:** Mid-pipeline `AskUserQuestion("which approach should I take?")`.

### BP-027: Input gate before classify (`skill-spec-validator` runs first)
**Source:** Carter's hands-off vision
**Why:** Single chokepoint for human-required clarity. Validator either green-lights or returns surgical gap-fills with line numbers and required-field hints. Keeps downstream pipeline confident-and-quiet.
**When applicable:** Driver (`skill-factory`).
**Enforced by:** `skill-spec-validator` (Phase 1 of driver)
**Correct:** Phase 1 invokes validator. STATUS: pass → continue. STATUS: gaps → exit cleanly with fix-list.
**Incorrect:** Driver classifies first, then asks user 5 follow-up questions about the spec.

### BP-028: BLOCKER convention — sub-skills never silently fail
**Source:** Plan §Data contract
**Why:** A sub-skill that hits ambiguity it can't resolve writes `BLOCKER: <question>` as the first line of `notes.md`. Driver detects, exits cleanly to gap-report (treats as validator miss), and the validator improves on next run. No silent failures, no half-done outputs.
**When applicable:** Every sub-skill.
**Enforced by:** `skill-compliance-gate` (rejects outputs with `BLOCKER:` present); driver routing logic.
**Correct:** Sub-skill blocked on missing field writes `BLOCKER: spec.outputs.path is unspecified — required for transformation archetype.` Exits.
**Incorrect:** Sub-skill guesses, produces output, downstream compliance fails, root cause buried.

---

## Authoring discipline (meta-patterns about how the factory itself is built)

### BP-029: Build incrementally — one piece deeply, never scaffold-then-fill
**Source:** `feedback-incremental-build-not-scaffold-first.md`; Carter's pushback in Phase 4 round 3
**Why:** Scaffolding all sub-skills as empty stubs hides unfinished work and removes review checkpoints. Each stage produces a working, committed, reviewable artifact — never a half-built skeleton.
**When applicable:** Adding any new sub-skill, archetype, or factory feature.
**Enforced by:** Stage cadence rules in `~/.claude/plans/yeah-let-s-go-ahead-kind-nest.md`; reviewer discipline.
**Correct:** Stage 3 ships `skill-spec-validator` end-to-end with fixtures, tests, integration. Stage 4 starts only after Stage 3 review.
**Incorrect:** Stage 0 creates 15 empty `skill-X/` dirs, then iterates filling each.

### BP-030: Pattern first, code second; sub-skill catalog entry first, code second
**Source:** Stage cadence rules
**Why:** Documentation enables, not documents-after. A pattern that can't be articulated clearly enough for `PATTERNS.md` isn't a pattern — it's a vibe. A sub-skill without a `SKILLS.md` entry can't be reasoned about by collaborators.
**When applicable:** Every PR to `skill-factory`.
**Enforced by:** `CONTRIBUTING.md` workflow; CI compliance check (when added).
**Correct:** PR adds BP-### entry → second PR adds the sub-skill code that enforces it.
**Incorrect:** PR adds new sub-skill behavior without updating PATTERNS.md or SKILLS.md.

### BP-032: Fixtures live at the skill root as `fixtures/`, not under `references/`
**Source:** Stage 3 of skill-factory build (2026-04-22); surfaced by `/skill-compliance` flagging `references/fixtures/` as a nested-reference violation.
**Why:** `references/fixtures/` appears nested under `references/`, which triggers the BP-008 "one level deep" compliance warning. Fixtures are test data (not reference content the skill loads during live invocations), so they belong parallel to `references/`, following the BP-009 pattern. This keeps `references/` flat and the compliance check clean.
**When applicable:** Every sub-skill that ships with fixtures (all of them, per stage-cadence rule "no sub-skill ships without fixtures").
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

### BP-031: Co-locate tools that co-evolve in the same repo
**Source:** `feedback-colocate-co-evolving-tools.md`; Carter's Phase 4 round 2 requirement to migrate `/skill-compliance` into the factory repo
**Why:** When a tool and the rules it enforces evolve together, separate repos create stale-rubric problems. New best-practice → new compliance rule → new sub-skill behavior should ship as one PR, not three coordinated ones.
**When applicable:** Any meta-tool (factory) and the rule artifacts it operates on.
**Enforced by:** Repo organization decisions; reviewer discipline.
**Correct:** `skill-compliance` lives in `~/Projects/skill-factory/skill-compliance/` alongside `PATTERNS.md`.
**Incorrect:** `skill-compliance` in a separate repo while patterns evolve here.

---

## Pattern numbering reservations

- BP-001 to BP-099: stable, currently in use
- BP-100 to BP-199: archetype-specific patterns (added as new archetypes ship)
- BP-200+: experimental / deprecated patterns kept for historical reference

When deprecating a pattern, mark it `**Status: deprecated as of YYYY-MM-DD — see BP-NNN for replacement.**` Don't delete; downstream code may still reference the number.
