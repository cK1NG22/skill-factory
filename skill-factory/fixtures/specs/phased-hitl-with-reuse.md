# Client Skill Spec — board-prep

## Company
acme

## Skill slug
board-prep

## One-line description
Prepares a board meeting packet through a six-step interactive workflow.

## Trigger phrases
- "prep the board packet"
- "board prep"
- "build board packet"
- "assemble board materials"
- "run board prep"
- "get the board packet ready"

## Inputs
A path to a YAML agenda file describing meeting topics.

## Outputs
A `.docx` file at `~/Claude/board-prep/<meeting-date>-packet.docx`.

## Happy-path walkthrough
1. Read the agenda YAML. Ask the user to confirm each topic before proceeding.
2. For each topic, prompt the user for talking points. Wait for the user before moving on.
3. Fetch prior-period financials from the reference lookup table.
4. Consult the scoring rubric in the reference framework to rank risks.
5. Assemble the packet using `/docx` to render the final document.
6. Present a preview and ask the user to confirm before writing the output.

## Success signals
- The output `.docx` file exists at the expected path.
- The document contains one section per agenda topic.
- Prior-period financials appear in the packet.

## Failure modes
- **Agenda YAML malformed** → fail-fast with the offending line number.
- **`/docx` unavailable** → write BLOCKER per BP-028.
- **User abandons at any hard gate** → exit cleanly, preserve partial work.

## Existing skills to reuse
- `/docx` — renders the final packet document.
