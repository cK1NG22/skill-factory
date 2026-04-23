# BP-017: KPIs are Observable, Specific, Not gameable, Not compound

**Source:** `feedback-kpi-stress-test.md`; emerged from `/kpi-setter` testing
**Category:** KPIs & evaluation (Universal — artifact discipline)

**Why:** Vague KPIs ("self-contained", "complexity matches") can't be reliably evaluated by a grader. Each KPI must be checkable from the output alone (Observable), point at a concrete artifact (Specific), resist surface-compliance hacks (Not gameable), and test ONE thing (Not compound). **Promoted to Universal in Stage 3.5 (v3):** writing a well-formed `kpi.md` is cheap and makes every skill autoresearch-ready even if `/autoresearch` never runs against it.

**When applicable:** Every skill (Universal — artifact). Factory produces `kpi.md` for every client skill. **Running** autoresearch against kpi.md is a separate concern, gated by the `--polish-autoresearch` CLI flag, not by this BP.

**Enforced by:** `skill-kpi-design` (auto-runs the stress-test before presenting KPIs). See BP-018 for the meta-guard on when `/autoresearch` can consume kpi.md.

**Correct:** `KPI: output.yaml contains a "trigger_phrases" key with ≥5 string entries.`

**Incorrect:** `KPI: trigger phrases are good.`
