# Client Skill Spec — acme-board-memo

<!--
  EXAMPLE SPEC. This is a reference specimen of a complete, validator-passing
  client-spec.md. Use it alongside `client-spec-template.md` as a concrete
  illustration of what each section looks like when filled in for a real
  transformation-style skill.

  Scenario: Acme's chief of staff wants to turn markdown outlines of board
  memos into consistently-branded .docx documents (cover page, table of
  contents, styled headings, confidential footer) without hand-formatting
  each one in Word.
-->

## Company
acme

## Skill slug
board-memo

## One-line description
Generates a formatted .docx board memo from a markdown outline using Acme's cover page and section styling.

## Trigger phrases
- "generate board memo"
- "board memo from this"
- "make a board memo"
- "turn this into a board memo"
- "render as board memo"
- "acme board memo"
- "board memo docx"

## Inputs
A path to a `.md` file containing a board memo outline. The markdown file MUST include four top-level sections in this order: `# Title`, `## Summary`, `## Discussion`, `## Recommendation`. An optional YAML front-matter block (delimited by `---`) may supply two keys: `meeting_date` (ISO-8601 date string) and `author` (string).

## Outputs
A `.docx` file at `~/Claude/board-memo/<input-stem>.docx`. The document contains, in order: (1) an Acme-branded cover page with the title, meeting date, and author pulled from the input; (2) an auto-generated table of contents; (3) the four required sections styled with Acme's `SectionHeader` paragraph style; (4) a "CONFIDENTIAL — BOARD EYES ONLY" repeating footer on every page. On success, prints the absolute output path to stdout.

## Happy-path walkthrough
1. Read the input `.md` file from the path argument. Fail fast with exit code 1 if the path does not exist.
2. Parse the optional YAML front-matter block. Capture `meeting_date` and `author` if present. Leave each field empty if the block is absent or the key is missing.
3. Validate that all four required top-level sections (`# Title`, `## Summary`, `## Discussion`, `## Recommendation`) are present. Fail fast with a specific error naming the missing section if any is absent.
4. Invoke the `/docx` skill to construct a new document. Populate the Acme cover-page template with the title from `# Title`, the meeting date from front-matter (or `TBD` if absent), and the author from front-matter (or `TBD` if absent).
5. Insert an auto-generated table of contents on the page immediately after the cover.
6. For each of Summary, Discussion, and Recommendation: write the content under an H1 styled with Acme's `SectionHeader` paragraph style. Preserve inline bold, italic, hyperlinks, and bulleted lists from the source markdown.
7. Add a repeating page footer reading "CONFIDENTIAL — BOARD EYES ONLY" in 10pt red Acme-brand type on every page including the cover.
8. Ensure the output directory `~/Claude/board-memo/` exists. Create it if missing.
9. Write the finished `.docx` to `~/Claude/board-memo/<input-stem>.docx`.
10. Print the absolute output path to stdout. Do not auto-open the file.

## Success signals
- The output `.docx` file exists at `~/Claude/board-memo/<input-stem>.docx` after the skill completes.
- `file <output-path>` reports the output as a Microsoft Word document.
- Opening the output in Word shows a cover page on page 1 populated with the title plus either the front-matter values or `TBD` placeholders for meeting date and author.
- Every page carries the footer text "CONFIDENTIAL — BOARD EYES ONLY".
- The four required sections appear in order (Title on cover, then Summary, Discussion, Recommendation) with the `SectionHeader` style applied.

## Failure modes
- **Input file missing or unreadable** → fail-fast with exit code 1 and an error naming the missing path.
- **Input is missing one or more of the required top-level sections** → fail-fast with a specific error naming the missing section (for example, `missing required section: ## Recommendation`).
- **Front-matter block is malformed YAML** → prompt the user: "Front-matter YAML is malformed at line N. Fix and retry, or remove the front-matter block to fall back to TBD placeholders." Do not write any output.
- **`/docx` skill unavailable** → write `BLOCKER: /docx skill not installed` to `notes.md` per BP-028 and exit cleanly without writing any `.docx` output.
- **Output directory cannot be created** (permission denied) → fail-fast with the permission error and the target path.

## Existing skills to reuse
- `/docx` — existing ecosystem skill that handles all `.docx` writing. This skill is an opinionated Acme-branded template layer on top of `/docx`.

## Edge cases
- Input with no front-matter block → cover page shows `TBD` for meeting date and author.
- Summary, Discussion, or Recommendation section present but empty → render the heading with an empty body. Do not fail.
- Nested lists deeper than three levels → flatten to three levels; drop no content.
- Embedded fenced code blocks → render in a monospace style; apply no syntax highlighting.

## Anti-goals
- Do NOT include content in the output that is not present in the source markdown. No auto-summarization. No filler prose. No "AI-generated" additions.
- Do NOT modify the input markdown file under any circumstance.
- Do NOT ship a document without the CONFIDENTIAL footer. The footer is a hard requirement even when the input appears innocuous — the caller relies on it for downstream handling.

## Delivery
Remote repo: no
