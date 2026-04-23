# Expected output — gaps-input.md

When `skill-cron-observability` runs against `fixtures/gaps-input.md`, it should fail fast at Step 4 of its procedure (Scheduling section is missing cron frequency AND artifact extension).

## notes.md

Must contain a `BLOCKER:` line like:

```
BLOCKER: Scheduling section missing cron frequency or artifact extension
```

The exact wording may vary but must:
1. Begin with `BLOCKER:`.
2. Name the missing field(s) (cron frequency and/or artifact extension).
3. Implicate the upstream validator (a well-formed spec declares both).

## instrumentation-snippet.md

**NOT produced** — the sub-skill must refuse to fabricate a snippet from an incomplete Scheduling section.

## Why this fixture matters

- Proves strict-stop discipline (BP-028) — the sub-skill refuses to guess missing fields.
- Proves driver-contract enforcement — when `is_scheduled: true` fires but the spec's Scheduling section is skeletal, the sub-skill surfaces the contradiction upstream rather than silently inventing a default frequency or extension.
- Proves early-exit — the skill stops at Step 4 of its own procedure rather than producing a degraded snippet that would require hand-fixes before deployment.
