# Acme Onboarding Checklist Spec

## Company
acme

## Skill slug
onboarding-checklist

## One-line description
Guides a new hire through a phased onboarding checklist and emails HR when each phase is complete.

## Trigger phrases
- "onboard new hire"
- "new hire checklist"
- "run onboarding"
- "start onboarding for john"
- "acme onboarding"
- "onboarding for <name>"

## Inputs
- New hire name (prompt arg)
- Start date (prompt arg, ISO format)

## Outputs
- A markdown report at `~/Claude/acme-onboarding-checklist/<hire-slug>-status.md` summarizing completed phases.
- HR notification email sent per phase.

## Happy-path walkthrough
Read the new hire name and start date. Announce Phase 1. Ask the user to confirm paperwork is complete. On confirmation, invoke `/acme-generate-email` to send the HR notification. Move to Phase 2. Ask about IT setup. On confirmation, invoke `/acme-generate-email` again for IT confirmation. Continue through Phase 3 (benefits enrollment) with the same `/acme-generate-email` invocation pattern. Write final status to `~/Claude/acme-onboarding-checklist/<hire-slug>-status.md`. Report path to user.

## Success signals
- Status file exists at expected path
- HR received 3 notification emails (one per phase)
- Exit code 0

## Failure modes
- User doesn't confirm within 24 hours → write BLOCKER to session notes
- Email fails to send → retry once, then fail-fast
- `/acme-generate-email` not installed → fail-fast with install instructions

## Existing skills to reuse
/acme-generate-email
