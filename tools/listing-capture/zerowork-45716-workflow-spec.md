# ZeroWork Workflow 45716 Portable Spec

Source workflow: `https://creator.zerowork.io/workflows/45716`
Workflow title visible in editor: `ImportFromWeb`
Capture date: `2026-06-11`

This is a read-only reverse-engineering note. The workflow was opened in the ZeroWork editor, inspected node by node, and screenshotted. It was not run, duplicated, edited, deleted, or exported. Cookies, tokens, session storage, and credentials were not inspected. A sticky note on the canvas says `Use Cookie Editor`; this spec records only that visible note and does not include any cookie values.

## Evidence

Screenshots are saved under:

`tools/listing-capture/zerowork-45716-screenshots/`

Key screenshots:

- `00-full-canvas.png`: full workflow canvas.
- `01-start-repeat.png` through `13-get-bullets-2nd.png`: original per-node config-panel captures.
- `06-start-condition-retry.png`, `11-clear-data-retry.png`, `12-is-empty-retry.png`, `13-get-bullets-2nd-retry.png`: clearer re-captures for nodes whose first screenshot selected the node but did not expose all settings.

## End-To-End Logic

The workflow loops through an input ZeroWork table of Amazon listing links. For each input row it opens the Amazon link, derives a shortened canonical product URL, extracts the product title, extracts bullet text using a primary selector, falls back to a second selector if the primary bullet selector is empty, formats the bullet text into bullet form via ChatGPT, extracts the ASIN from the original input URL via ChatGPT, writes the output fields to a ZeroWork results table, then clears the temporary bullet variable.

The workflow does not visibly force marketplace through a separate country/locale node. Marketplace is inferred from the input URL and from the ChatGPT link-normalization prompt, which asks for `amazon.[country_code]/dp/[ASIN]`.

## Inputs

- Input table: `Input Link | ZeroWork Results`
- Input table/id shown in nodes: `86657`
- Input field: `Amazon Links`
- Backing Google Sheet: `https://docs.google.com/spreadsheets/d/1XkzBI6iULIra3STWawpMJnTTtNHbq54mWI3zXhKxPhU/`
- Backing Google Sheet title: `Amazon Scraping`
- Selected Google Sheet tab: `Input Link`
- Loop mode: Dynamic, `process table rows one by one`
- Loop order: normal order; `Newest rows first (reverse order)` is unchecked.
- Repetition limit: blank.
- Start row: blank.
- Auto-continue from last row: unchecked.
- Observed input rows begin with one column, `Amazon Links`, followed by URLs such as:
  - `https://www.amazon.com/dp/B09DCB77Z4`
  - `https://www.amazon.com/dp/B0FZT3W6KJ`
  - `https://www.amazon.com/dp/B07F1MHRKM`

## Output

- Output table: `Results | ZeroWork Results`
- Output table/id shown in nodes: `85772`
- Backing Google Sheet: `https://docs.google.com/spreadsheets/d/1XkzBI6iULIra3STWawpMJnTTtNHbq54mWI3zXhKxPhU/`
- Backing Google Sheet title: `Amazon Scraping`
- Selected Google Sheet tab: `Results`

Output column map:

| Output column | Source / logic |
| --- | --- |
| `link` | ChatGPT transforms `{Amazon Links}` into `amazon.[country_code]/dp/[ASIN]`. |
| `title` | Plain text from XPath `//*[@id="productTitle"]`. |
| `bullet_points` | Plain text from primary XPath `//*[@id="feature-bullets"]/ul`; if empty, fallback XPath `//*[@id="productFactsDesktopExpander"]/div[1]/ul`; then ChatGPT formats the captured variable into bullet form. |
| `ASIN` | ChatGPT extracts ASIN from `{Amazon Links}` and returns only the ASIN. |

Observed output tab columns are exactly:

`link`, `title`, `bullet_points`, `ASIN`

Example observed first result row:

- `link`: `amazon.com/dp/B09DCB77Z4`
- `title`: `Mens Slimming Compression Shirt, Body Shaper Workout Tank Top, Gynecomastia Tummy Control Undershirts - Change in Seconds`
- `ASIN`: `B09DCB77Z4`

## Selector Test

One read-only browser selector test was run against the first input URL, `https://www.amazon.com/dp/B09DCB77Z4`. ZeroWork itself was not run.

Observed:

- Amazon resolved the page to `https://www.amazon.com/dp/B09DCB77Z4?th=1&psc=1`.
- Title selector `#productTitle` worked.
- Primary bullet selector `#feature-bullets ul` returned empty.
- Fallback bullet selector `#productFactsDesktopExpander > div:first-child ul` returned 5 bullet items.

This confirms the workflow's `isEmpty` fallback branch is necessary for at least one current Amazon listing layout.

## Node-By-Node Spec

### 1. Start Repeat

- Node label: `Start Repeat`
- Node ID: `2029551`
- Node type/action: Logic / Start Repeat
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/01-start-repeat.png`
- Loop type: `Dynamic` selected; `Standard` unselected.
- Table to loop through: `Input Link | ZeroWork Results`
- Table/internal id: `86657`
- `Newest rows first (reverse order)`: unchecked.
- Repetition limit: blank.
- Start from row number: blank.
- Auto-continue from last row: unchecked.

### 2. Open Link

- Node label: `Open Link`
- Node ID: `2029568`
- Node type/action: Browser / Open Link
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/02-open-link.png`
- Link value: `{id: 86657, name: Amazon Links}`
- Open in a new tab: unchecked.
- Delay: min `1` sec, max `1` sec.
- Auth note: panel includes ZeroWork help text `What if the website requires login?`; no configured credential or cookie value was visible or copied.

### 3. Format Link

- Node label: `Format Link`
- Node ID: `2044271`
- Node type/action: External / Ask ChatGPT
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/03-format-link.png`
- Model: `gpt-3.5-turbo` / visible label `ChatGPT 3.5 legacy`
- Prompt:

```text
{id: 86657, name: Amazon Links}
Shorten the link into: amazon.[country_code]/dp/[ASIN]

For your response. Include ONLY the link and don't add any other word/s.
```

- Save answer to: `Results | ZeroWork Results`
- Output table/internal id: `85772`
- Output field: `link`

### 4. Get Title

- Node label: `Get Title`
- Node ID: `2029572`
- Node type/action: Web Interaction / Save Web Element
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/04-get-title.png`
- Web element selector: XPath `//*[@id="productTitle"]`
- Save as: `Plain text`
- Skip if no element is found: checked.
- Save to: `Results | ZeroWork Results`
- Output table/internal id: `85772`
- Output field: `title`
- Delay: min `1` sec, max `1` sec.

### 5. Get Bullets 1st

- Node label: `Get Bullets 1st`
- Node ID: `2040299`
- Node type/action: Web Interaction / Save Web Element
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/05-get-bullets-1st.png`
- Web element selector: XPath `//*[@id="feature-bullets"]/ul`
- Save as: `Plain text`
- Skip if no element is found: checked.
- Save to: Variables
- Variable/internal id: `85660`
- Variable name: `Bullet Points`
- Delay: min `1` sec, max `1` sec.

### 6. Start Condition

- Node label: `Start Condition`
- Node ID: `2040298`
- Node type/action: Logic / Start Condition
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/06-start-condition-retry.png`
- Value to compare to: Variables
- Variable/internal id: `85660`
- Variable name: `Bullet Points`
- Branching: connected to two `Set Condition` nodes, `isNotEmpty` and `isEmpty`.

### 7. isNotEmpty

- Node label: `isNotEmpty`
- Node ID: `2040307`
- Node type/action: Logic / Set Condition
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/07-is-not-empty.png`
- Comparison type: `Data found is not empty`
- Internal comparison value: `EXISTS`
- Branch meaning: primary bullet selector found data; skip fallback extraction and format the existing variable.

### 8. Format Bullets (Primary Branch)

- Node label: `Format Bullets`
- Node ID: `2045688`
- Node type/action: External / Ask ChatGPT
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/08-format-bullets-top.png`
- Model: `gpt-3.5-turbo` / visible label `ChatGPT 3.5 legacy`
- Prompt:

```text
{id: 85660, name: Bullet Points}

Kindly format it so that it will be in bullet form
```

- Save answer to: `Results | ZeroWork Results`
- Output table/internal id: `85772`
- Output field: `bullet_points`

### 9. Get ASIN

- Node label: `Get ASIN`
- Node ID: `2045689`
- Node type/action: External / Ask ChatGPT
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/10-get-asin.png`
- Model: `gpt-3.5-turbo` / visible label `ChatGPT 3.5 legacy`
- Prompt:

```text
{id: 86657, name: Amazon Links}
From this kindly extract the ASIN.

Include ONLY the ASIN in your resonse. Don't add other word/s.
```

- Save answer to: `Results | ZeroWork Results`
- Output table/internal id: `85772`
- Output field: `ASIN`
- Note: original prompt typo `resonse` preserved above.

### 10. Clear Data

- Node label: `Clear Data`
- Node ID: `2045815`
- Node type/action: Data / Update Data
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/11-clear-data-retry.png`
- Operation: `Set equal to the following value`
- Value: blank; placeholder says `Enter value or leave empty to clear the current value`
- Data to be updated: Variables
- Variable/internal id: `85660`
- Variable name: `Bullet Points`
- Branch placement: appears after `Get ASIN`; clears the temporary bullet variable before the next loop iteration.

### 11. isEmpty

- Node label: `isEmpty`
- Node ID: `2040300`
- Node type/action: Logic / Set Condition
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/12-is-empty-retry.png`
- Comparison type: `Data not found is empty`
- Internal comparison value: `NOT_EXISTS`
- Branch meaning: primary bullet selector did not find data; run the fallback bullet extraction.

### 12. Get Bullets 2nd

- Node label: `Get Bullets 2nd`
- Node ID: `2029957`
- Node type/action: Web Interaction / Save Web Element
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/13-get-bullets-2nd-retry.png`
- Web element selector: XPath `//*[@id="productFactsDesktopExpander"]/div[1]/ul`
- Save as: `Plain text`
- Skip if no element is found: checked.
- Save to: Variables
- Variable/internal id: `85660`
- Variable name: `Bullet Points`
- Delay: min `1` sec, max `1` sec.

### 13. Format Bullets (Fallback Branch)

- Node label: `Format Bullets`
- Node ID: `2044317`
- Node type/action: External / Ask ChatGPT
- Screenshot: `tools/listing-capture/zerowork-45716-screenshots/09-format-bullets-bottom.png`
- Model: `gpt-3.5-turbo` / visible label `ChatGPT 3.5 legacy`
- Prompt:

```text
{id: 85660, name: Bullet Points}

Kindly format it so that it will be in bullet form
```

- Save answer to: `Results | ZeroWork Results`
- Output table/internal id: `85772`
- Output field: `bullet_points`
- Then rejoins the shared `Get ASIN` and `Clear Data` path.

## Branch And Loop Logic

Main path:

1. `Start Repeat`
2. `Open Link`
3. `Format Link`
4. `Get Title`
5. `Get Bullets 1st`
6. `Start Condition`

Primary branch:

1. If `Bullet Points` exists, `isNotEmpty`
2. `Format Bullets` node `2045688`
3. `Get ASIN`
4. `Clear Data`
5. Continue next dynamic input row.

Fallback branch:

1. If `Bullet Points` does not exist, `isEmpty`
2. `Get Bullets 2nd`
3. `Format Bullets` node `2044317`
4. `Get ASIN`
5. `Clear Data`
6. Continue next dynamic input row.

No explicit retry, try/catch, captcha, rate-limit, or error-handling nodes were visible on the inspected canvas. Throttling visible in the web/open/extract nodes is `1` sec min and `1` sec max where configured.

## Portable Codex Reimplementation Notes

- Replace ChatGPT-based ASIN parsing with deterministic URL parsing where possible. Match `/dp/<ASIN>`, `/gp/product/<ASIN>`, and common Amazon redirect/listing URL variants.
- Replace ChatGPT-based link shortening with deterministic canonicalization: preserve marketplace host from the input URL and write `https://amazon.<tld>/dp/<ASIN>` or the exact no-scheme format if downstream consumers expect ZeroWork's original output style.
- Replace ChatGPT-based bullet formatting with deterministic splitting/cleanup of `<li>` text. Preserve one bullet per line.
- Extract title from `#productTitle`.
- Extract bullets first from `#feature-bullets ul`, then fall back to `#productFactsDesktopExpander > div:first-child ul`.
- Retain a per-row temporary `Bullet Points` variable equivalent and clear it after the row is written.
- Use DataDive MCP or another upstream source to provide the equivalent `Amazon Links` input list.
