---
name: acme-board-memo
description: Compose a one-page board memo from the standard Acme briefing template. Use when "draft a board memo", "acme board memo", or "write the Q[N] board update". Do NOT use for press releases or external comms.
allowed-tools:
  - Read
  - Write
  - Bash
---

# acme-board-memo

Compose a one-page board memo from the standard Acme briefing template.

## Happy-path walkthrough

1. Load the input briefing.
2. Identify the recommendation and three supporting points.
3. Draft the memo using the standard Acme template.
4. Write the memo to disk.

## Procedure

### Step 1 — Load briefing input

Read the briefing file passed by the caller and confirm the leadlines exist.

### Step 2 — Draft the memo

Compose the memo body in the standard Acme template format.

### Step 3 — Write to disk

Save the memo to the target path and return the result.
