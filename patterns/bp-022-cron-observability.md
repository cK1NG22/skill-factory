# BP-022: Cron/scheduled skills must expose: last-run, success, artifact location

**Source:** `feedback-automation-observability.md`
**Category:** Output & rendering (Conditional — trait: `is_scheduled`)

**Why:** Automated processes are invisible until they break. Every cron-archetype skill must answer three questions on demand: when did it last run, did it succeed, what did it produce. Without this, debugging requires log archaeology.

**When applicable:** Skills with a scheduling section in spec (trait: `is_scheduled`).

**Enforced by:** `skill-cron-observability`

**Correct:** Skill writes `~/Claude/<skill>/runs/<timestamp>/{result.json, artifact.X}` and a top-level `latest.json` symlink.

**Incorrect:** Cron skill emits to syslog only; user has no way to check status.
