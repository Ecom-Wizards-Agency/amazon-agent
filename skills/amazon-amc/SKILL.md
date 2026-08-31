---
name: amazon-amc
description: "Write, validate, run, and schedule Amazon Marketing Cloud SQL through AdLabs, including privacy-safe measurement queries and audience definitions."
---

# Amazon Marketing Cloud

Browser: None (AdLabs MCP plus local SQL validation).

Use this skill for Amazon Marketing Cloud SQL, AMC measurement workflows, scheduled AMC queries, and AMC audiences. Ordinary Amazon Ads reporting and PPC diagnosis remain in `amazon-reporting` and `amazon-audit`.

## Route The Request

1. Identify the requested outcome: draft SQL, validate SQL, one-time query, recurring schedule, or audience.
2. Start one AdLabs chat session and read `adlabs://instructions`, `adlabs://guides/amc_sql`, and `adlabs://docs/amc_actions`. Current AdLabs documentation overrides this repository when the execution contract changes.
3. Resolve the exact team and profile. Confirm AMC is connected to that profile before promising execution.
4. Call AMC `get_data_sources` before using a table or field. AMC schemas vary by profile; a static example never proves availability.
5. Read [references/sql-contract.md](references/sql-contract.md). For a starting point, adapt [references/starter-queries.sql](references/starter-queries.sql) only after checking its tables and fields against the selected profile.
6. Validate custom SQL locally:

   ```bash
   python3 tools/amazon-amc/validate_sql.py <query.sql> --mode query
   python3 tools/amazon-amc/validate_sql.py <audience.sql> --mode audience
   ```

7. Drafting and validation are the default. Do not execute, schedule, create, update, or delete anything unless the operator asked for that exact action.

## Execution Gates

- **One-time query:** ask for the query name and date range before creating the workflow execution. A one-time run consumes AMC resources and is not implied by a request to write SQL.
- **Recurring query:** confirm the name, date behavior, cadence, and immediate first run before creating a schedule. Scheduling is a persistent write.
- **Audience:** confirm the exact scope, name, date window or lookback, refresh cadence, and whether it is rule-based or lookalike. Preview a library audience's resolved SQL before creation. Audience SQL follows different date rules from measurement SQL.
- **Deletion or update:** identify the exact execution, schedule, or audience and obtain explicit confirmation. Never infer the target from a similar name.

After starting a run, poll the existing execution rather than creating a duplicate. A pending or running status is not a failure. Fetch results only after the run succeeds.

## Output

For a draft, return the SQL plus its required tables, fields, parameters, privacy caveats, and validation result. For an execution, also report the selected profile, mode, name, date range, status, and result reference without exposing credentials or internal tokens.
