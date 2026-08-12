# Source Inventory

TEMPLATE. Copy into the client's context pack and fill in. Locators, permissions and IDs
stay in that copy, never in this repository.

## Coverage

- Coverage level: <Directional | Reliable | Audited>.
- Sources checked: <list>.
- Missing high-value lanes: <what could not be answered, and what it would take>.
- Rejected or lower-confidence candidates: <what was considered and turned down, with the
  reason, so it is not re-litigated next time>.

## Sources

| Source | Type | Locator | Connector Or Tool | Permission Status | Last Checked | Supports | Gaps Or Caveats | Automation Eligible | Update Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <name> | <type> | <link or path, in the client pack only> | <connector> | <status> | <YYYY-MM-DD> | <what it can answer> | <what it cannot> | <yes/no/partial> | <read-only, propose-only, or refresh-on-request> |

The update boundary column is the one that gets skipped and matters most. It records what an
agent may do to the source unasked, and "propose updates, do not overwrite" is a different
instruction from "read-only".

## Update Guidance

- Default refresh cadence: <ad hoc, or the agreed cadence>.
- Refresh order for a new forecast: actuals first, market data second, strategy last.
- Do not create recurring polling unless the operator explicitly asks for it.
- Do not inspect email by default.
