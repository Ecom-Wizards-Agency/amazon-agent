# AdLabs Dayparting Execution

Read the current `adlabs://docs/dayparting_actions` resource before operating. It is the execution authority.

## Before A Write

1. Start one AdLabs chat session and read `adlabs://instructions`.
2. Resolve the exact team and profile and verify the profile timezone.
3. List existing dayparting schedules and check whether the target campaigns are already assigned.
4. Read the current schedule before editing it. Unmentioned cells on an update keep their stored values.
5. Render the proposed grid with `dry_run=true`.
6. Show the schedule name, state, timezone, campaign count, changed-cell count, minimum and maximum percentage, and the warning below.
7. Obtain explicit approval for the exact create, update, assignment, pause, clone, or delete operation.

Required warning:

> While dayparting is assigned, make bid changes in AdLabs. Bid changes made elsewhere can be overwritten because the schedule continues to multiply its stored base bid.

## Units And Timing

- Grid cells are whole percentages. `20` means +20%, `-25` means -25%, and `0` means base bid.
- Accepted values are -99 through 300.
- Grid hours use the profile's local timezone.
- A write does not immediately prove live bids changed. It applies on the next AdLabs hourly run.
- Assignment is separate from schedule creation. A created schedule affects nothing until campaigns are assigned.

## Safer Operations

- Create or update: dry run first, then one approved write.
- Pause: preserves the grid and rolls bids back asynchronously.
- Delete: destructive and not recoverable. Prefer pause unless deletion is explicitly required.
- Clone: validate the resulting grid and name collision in dry-run mode.
- Timeout: re-read schedules before retrying. A timed-out create may already have succeeded.

Do not report bids as restored or applied until the relevant subsequent state is observable. Logs do not prove every asynchronous rollback.
