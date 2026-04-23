# Client Skill Spec — convert-md-to-docx

## Company
acme

## Skill slug
convert-md-to-docx

## One-line description
Converts a markdown file to a formatted .docx document using the existing /docx writer.

## Trigger phrases
- "convert markdown to docx"
- "md to word doc"
- "turn this md into word"
- "markdown to word"
- "make a word doc from this md"
- "export markdown as docx"
- "render md as word"

## Inputs
A path to a `.md` file (relative or absolute). File must be a well-formed markdown document (no binary payloads). Optional second argument: output filename (defaults to input stem + `.docx`).

## Outputs
A `.docx` file at `~/Claude/convert-md-to-docx/<input-stem>.docx`. On success, prints the full output path to stdout so the user can open it immediately.

## Happy-path walkthrough
1. Read the input `.md` file from the path argument. If the path doesn't exist, fail fast with a clear error.
2. Parse the markdown into an AST: headings (levels 1-6), paragraphs, ordered and unordered lists, fenced code blocks (preserve language), inline code, bold/italic, links, and tables.
3. Invoke the `/docx` skill via its standard API to construct a new .docx document from the AST. Map each markdown element to its docx analogue (heading styles, list styles, code style, link hyperlinks, table grids).
4. Ensure the output directory `~/Claude/convert-md-to-docx/` exists. Create it if missing.
5. Write the .docx to `~/Claude/convert-md-to-docx/<input-stem>.docx`, where `<input-stem>` is the input filename without extension.
6. Print the absolute output path to stdout. Do NOT auto-open the file.

## Success signals
- The output .docx file exists at the expected path after the skill completes.
- `file <output-path>` reports the output as a Microsoft Word document.
- Opening the .docx in Word shows all headings rendered at the correct level (h1 → Heading 1, etc.).
- Tables from the input render as Word tables, not as plaintext.
- Code blocks render in a monospace font with preserved indentation.

## Failure modes
- **Input file missing or unreadable** → fail-fast with exit code 1 and an error message naming the missing path.
- **Input file is not valid markdown** (binary, 0 bytes, 50MB+) → fail-fast with a specific error naming what's wrong.
- **`/docx` skill unavailable** → write `BLOCKER: /docx skill not installed` per BP-028 and exit cleanly.
- **Output directory cannot be created** (permission denied) → fail-fast with the permission error and the path.

## Existing skills to reuse
- `/docx` — handles the .docx writer; this skill is a thin adapter layer around it.

## Edge cases
- Markdown files with deeply nested lists (5+ levels) should flatten to Word's max list depth without losing content.
- Code blocks without a language tag should render as plain monospace (no syntax highlighting).
- Tables with unbalanced columns (rows of different lengths) should normalize to the widest row.

## Anti-goals
- Do NOT auto-convert pasted URLs into hyperlinks in prose — only explicit markdown link syntax `[text](url)` becomes a hyperlink.
- Do NOT include a title page, table of contents, or any content not present in the source markdown.
- Do NOT modify the input file under any circumstance.
