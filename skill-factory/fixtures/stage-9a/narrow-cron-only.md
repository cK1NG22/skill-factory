# weekly-digest (narrow-cron-only spec)

Stage 9a fixture. Designed to fire **only** the `is_scheduled` trait in
the classifier. No Reference exemplars, no `/<skill>` reuse, no HITL
prompts, no numbered walkthrough items (prose-only walkthrough).

## Company

acme

## Skill slug

weekly-digest

## One-line description

Produces a weekly markdown digest of the team's engineering activity, scheduled every Friday at 4pm UTC. Use when "weekly digest", "engineering recap", "what shipped this week".

## Trigger phrases

- weekly digest
- engineering recap
- what shipped this week
- run weekly digest
- generate the weekly summary

## Inputs

- A configured list of git repository paths in `~/.config/weekly-digest/repos.txt`. Read once per run.

## Outputs

- A markdown digest at `~/Claude/acme-weekly-digest/runs/<timestamp>/artifact.md` summarizing commits, authors, and files touched in the last 7 days.

## Happy-path walkthrough

The cron daemon fires the script at the scheduled time. The script reads the configured repository list, then runs `git log --since="7 days ago"` against each repository to enumerate commits, authors, and changed file paths. It groups commits by author, formats a markdown digest with a header per repository, writes the digest artifact to the runs directory, then writes the BP-022 observability records — `result.json` plus the `latest.json` symlink update. The script exits with code 0 on success, code 1 on any git fetch failure.

## Success signals

- A new directory appears under `~/Claude/acme-weekly-digest/runs/<timestamp>/` every Friday at 16:00 UTC, containing both `artifact.md` and `result.json`.
- The `~/Claude/acme-weekly-digest/latest.json` symlink resolves to the most recent run's `result.json`.
- The artifact's repository sections are alphabetized and each lists at least one commit (or an explicit "no commits this week" note).

## Failure modes

- **Git log fetch fails for one or more repositories** → the script records `success: false` in `result.json`, includes the failed repository in the artifact under a "## Fetch failures" heading, and does NOT update `latest.json`.
- **Repository config missing or empty** → the script writes `BLOCKER: repos.txt is missing or empty; cannot generate digest without repository list` to `notes.md` and stops without writing an artifact.
- **Disk full during artifact write** → the script catches the OSError, writes `result.json` with `success: false`, and surfaces the disk-full condition in the runs directory's `notes.md`.

## Existing skills to reuse

None.

## Scheduling

- **Cron frequency:** `0 16 * * 5` (Fridays at 16:00 UTC).
- **Artifact extension:** `.md`.
- **Skip overlapping runs:** if a previous Friday's run is still in progress (presence of an in-flight `runs/<timestamp>/.lock` file), the new run aborts cleanly with `success: false` and skips the digest.
