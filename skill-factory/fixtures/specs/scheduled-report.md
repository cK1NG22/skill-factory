# Client Skill Spec — nightly-inventory

## Company
acme

## Skill slug
nightly-inventory

## One-line description
Generates a nightly inventory snapshot report from the warehouse database.

## Trigger phrases
- "nightly inventory"
- "run inventory snapshot"
- "generate inventory report"
- "inventory snapshot"
- "tonight's inventory report"

## Inputs
Warehouse database connection string from `~/.config/acme/warehouse.env`.

## Outputs
A `.json` snapshot at `~/Claude/nightly-inventory/<YYYY-MM-DD>.json` and a `latest.json` symlink.

## Happy-path walkthrough
1. Read the warehouse connection string from the env file.
2. Query the `inventory` table for current stock levels.
3. Compare against yesterday's snapshot to compute deltas.
4. Write the snapshot to the dated JSON file.
5. Update the `latest.json` symlink.
6. Write a run log entry to `runs/<timestamp>/result.json`.

## Success signals
- The dated JSON snapshot exists.
- `latest.json` points at the newest dated snapshot.
- The run log contains a success entry.

## Failure modes
- **Database unreachable** → retry 3 times with exponential backoff; then BLOCKER.
- **Env file missing** → fail-fast with the missing path.

## Existing skills to reuse
None

## Scheduling
Runs nightly at 02:00 via cron. Recurring daily.
