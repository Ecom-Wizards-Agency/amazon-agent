# Cold-Start Automation Prompts

Future automation runs have no conversation history. Resolve `{project_root}` and `{config_path}` during setup and store these exact prompts in the schedules.

## Weekly Prompt

```text
Run the configured weekly Amazon operational check. Load the shared skill at {project_root}/skills/amazon-operations-review/SKILL.md and read its weekly-check, shipment-exceptions, and review-tracking references completely. Load {config_path}. If setup state is not active or configuration is missing, stop without opening Amazon or writing external data. Run weekly mode only. Verify every account and marketplace before reading data. Update the shared Review Management workbook and task system with update-not-duplicate behavior. Post one compact summary only to the configured internal Slack destination. Do not run full reshipment planning or submit shipment reconciliation. Stop before messages, refunds, promotions, listing edits, uploads, support cases, or shipment actions. Finish with accounts checked, clean checks, new findings, updated findings, tasks, skipped accounts, blockers, and external writes performed.
```

## Monthly Prompt

```text
Run the configured monthly Amazon operational check. Load the shared skill at {project_root}/skills/amazon-operations-review/SKILL.md and read its monthly-check reference completely. Load {config_path}. If setup state is not active or configuration is missing, stop without opening Amazon or writing external data. Run monthly mode only. Verify every account and marketplace before reading data. Apply the return-rate and recent-reshipment rules exactly. Update the task system with update-not-duplicate behavior and post one compact summary only to the configured internal Slack destination. Do not repeat weekly fee or review checks. Stop before promotions, listing edits, uploads, messages, refunds, or shipment actions. Finish with accounts checked, clean checks, new findings, updated findings, tasks, skipped accounts, blockers, reused reshipment evidence, and external writes performed.
```
