---
description: Set up, run, show, pause, or resume the gated weekly and monthly Amazon operational checks
argument-hint: "setup|weekly|monthly|show|pause|resume"
---

# Amazon Operational Checks

Load and follow the `amazon-operations-review` skill as the source of truth.

The requested action is: **$ARGUMENTS**

Map actions as follows:

- `setup`: treat as `Set up the operational checks`. Preview only and stop before creating an automation.
- `weekly`: treat as `Run the weekly operational check now`.
- `monthly`: treat as `Run the monthly operational check now`.
- `show`: treat as `Show the operational checks setup`.
- `pause`: treat as `Pause the operational checks`.
- `resume`: treat as `Resume the operational checks` and require confirmation after showing both future schedules.

Only the exact approval `Approve and activate operational checks`, following a complete pending preview, authorizes creation and activation of the two recurring automations. Activation must not trigger an immediate operational run.
