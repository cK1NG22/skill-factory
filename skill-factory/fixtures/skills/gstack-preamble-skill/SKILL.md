---
name: gstack-preamble-skill
description: Fixture for edge case 3 — opens with bash preamble that includes false-positive /<skill> paths that must be skipped before scanning invokes_skills.
allowed-tools:
  - Bash
  - Read
---

# gstack-preamble-skill

```bash
_GSTACK_ROOT="$HOME/.claude/skills/gstack"
source "$_GSTACK_ROOT/bin/gstack-update-check"
eval "$(~/.claude/skills/gstack/bin/gstack-telemetry-log init)"
export _GSTACK_SESSION_ID=$(~/.claude/skills/gstack/bin/gstack-session-id)
if [ "$_GSTACK_ROOT/bin/gstack-dispatch" ]; then
  source "$_GSTACK_ROOT/bin/gstack-dispatch"
fi
```

## Purpose
A fixture skill that exercises the gstack-preamble-skip rule. The preamble above contains `/gstack`, `/bin`, etc inside bash paths. These MUST be excluded from the `invokes_skills` scan. The body below this heading is where real invocations live.

## Procedure
Read the input. Process it using local logic. Write the output. No Agent invocations of other skills.
