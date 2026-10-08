# Collecting Slack threads for the knowledge sweep

A collection agent reads one channel (or one DM) for one time window and writes thread records into the gitignored sweep store. It decides only whether a thread is worth carding later; it never writes a card or a unit, never posts to Slack, and never writes outside `_local/knowledge-sweep/`.

## Where things go

- Thread records: `_local/knowledge-sweep/threads/<channel_id>/<thread_ts>.json`, one per thread, following `tools/knowledge/thread.schema.json`.
- Skipped parents: `_local/knowledge-sweep/skipped/<channel_id>/<window>.jsonl`, one JSON line per parent message not stored: `{"ts": "...", "reason": "six words at most"}`. Bot posts, report digests, greetings, scheduling, non-Amazon chatter and design feedback are the usual reasons.
- Window checkpoint: `_local/knowledge-sweep/checkpoints/<channel_id>-<window>.json` with `channel_id`, `channel_name`, `family`, `window` (for example `2026-H1`), `oldest`, `latest`, `pages_read`, `parents_seen`, `threads_stored`, `parents_skipped`, `complete` (true only when every page in the window was read), `notes`.

## How to read

1. Read the channel newest to oldest with `slack_read_channel` (detailed format, limit 100) bounded by the window's `oldest` and `latest` Unix timestamps, following `cursor` until the page is exhausted. Count every parent.
2. A parent is a candidate when all of these hold: a human wrote it or a human replied in its thread; the subject is Amazon operations (Seller Central, FBA or FBM, listings, catalog, Brand Registry, compliance, support cases, Account Health, pricing, Ads console or campaigns, reports); and a team member took part (Victor, João or Danica, or their IDs from the sweep config) or the thread shows a diagnosis or a fix.
3. For each candidate, read the full thread with `slack_read_thread` and write the record with every reply verbatim. A parent with no replies is still a candidate when the parent itself carries the diagnosis or the fix.
4. Fill `first_glance` honestly: `amazon_operational`, the best `topic_guess`, `has_resolution_hint` (someone states an outcome), `language`.
5. Record identifiers as they appear. Records live only in the gitignored store; stripping happens later, at card and unit level.

## Do not

- Do not summarise, translate or shorten message text in a record.
- Do not read channels or windows outside your assignment.
- Do not mark a checkpoint complete when a page failed or a cursor was lost; set `complete: false` and say which range is missing in `notes`.
