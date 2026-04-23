# BP-018: KPI before autoresearch — never run autoresearch without `kpi.md`

**Source:** `hub-skills-tooling.md` rules
**Category:** KPIs & evaluation (Meta — factory polish guard)

**Why:** `/autoresearch` grades against `kpi.md`. Without one, the optimizer has no gradient and produces garbage edits. The kpi.md must exist and pass stress-test BEFORE the optimization loop runs. Post-v3 this is trivially satisfied because BP-017 is Universal (every skill has kpi.md) — BP-018 remains as an explicit safety rail against future regressions.

**When applicable:** Whenever `--polish-autoresearch` is passed to `/skill-factory`, or when `/autoresearch` is invoked standalone. Factory-internal guard; not applied to client skill content.

**Enforced by:** `skill-autoresearch-gate` (refuses to proceed without `kpi.md`).

**Correct:** Author runs `/skill-kpi-design` → produces `kpi.md` → then `/autoresearch <skill>`.

**Incorrect:** Author runs `/autoresearch <skill>` with no kpi.md; loop produces noise.
