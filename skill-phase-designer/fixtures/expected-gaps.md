# Expected output — gaps-input.md

When `skill-phase-designer` runs against `fixtures/gaps-input.md`, it should fail fast at Step 4 of its procedure (walkthrough has only 2 numbered items; `has_phases` should not have fired).

## notes.md

Must contain a `BLOCKER:` line like:

```
BLOCKER: walkthrough has <3 steps; has_phases should not have fired
```

The exact wording may vary but must:
1. Begin with `BLOCKER:`.
2. Name the "<3 steps" condition.
3. Implicate the upstream classifier (not silently invent missing steps).

## output.md

**NOT produced** — or produced empty / without a valid Procedure section. Acceptance is "no full Procedure section generated from a 2-step walkthrough".

## Why this fixture matters

- Proves strict-stop discipline (BP-028) — the sub-skill refuses to fabricate missing walkthrough content.
- Proves driver-contract enforcement — when the classifier's `has_phases: true` verdict disagrees with the walkthrough's actual step count, the sub-skill surfaces the contradiction rather than silently compensating.
- Proves early-exit — the skill stops at Step 4 of its own procedure rather than running through a degraded path that would produce a nonsense Procedure.
