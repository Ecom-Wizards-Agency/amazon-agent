---
description: Sweep Slack threads into knowledge cards, review them, promote ticked cards into units and write the run note (attended)
argument-hint: "[family, window or topic] (e.g. 'client_current since 2026-04, logistics batch 10'; empty = plan and stats only)"
---

# /knowledge-sweep: Slack threads to knowledge units

Turn resolved Amazon questions in Slack into anonymised units under `knowledge/<topic>/`.
The rules, the unit format, the roles that tick and the privacy line are in
`docs/knowledge-library.md`. Every working file stays in the gitignored
`_local/knowledge-sweep/` store; the sweep config there (`config.json`) holds the channel
families, team and bot IDs and is never copied into a tracked file.

Run it attended. Load the `amazon-sop-maintenance` skill before step 6; its Knowledge Units
section owns unit editing.

## Steps

1. **Plan.** `python3 tools/knowledge/slack_collect.py plan --config _local/knowledge-sweep/config.json`
   (add `--family F`, `--since YYYY-MM` or `--json`). Each line is one channel and window
   with its `oldest` and `latest` Unix timestamps and the checkpoint status. Pick the
   missing or partial windows for this session.
2. **Collect.** Hand each channel and window to a collection agent with
   `tools/knowledge/prompts/collect-threads.md` and the window's timestamps. Agents read
   Slack only and write thread records, skipped parents and checkpoints into the store. No
   agent posts, reacts or reads outside its window.
3. **Check the store.** `python3 tools/knowledge/slack_collect.py validate` (schema
   `tools/knowledge/thread.schema.json`) and `python3 tools/knowledge/slack_collect.py stats`
   (windows complete, partial and missing per family and channel, and channels with no
   checkpoint). Send a partial window back to step 2.
4. **Score.** `python3 tools/knowledge/slack_collect.py candidates [--min-score N]` writes
   `candidates.jsonl` and prints counts per topic and family. The lexicon is
   `tools/knowledge/topics.json`.
5. **Extract, one topic at a time.**
   - `python3 tools/knowledge/extract_cards.py next --topic <topic> --batch 10` prints each
     thread with user IDs and timestamps, then the scrubbed preview of what must not
     reach a unit.
   - For a thread worth a card: `python3 tools/knowledge/extract_cards.py scaffold --thread <channel_id>:<thread_ts>`,
     then the extraction agent fills the card per `tools/knowledge/prompts/extract-card.md`.
   - `python3 tools/knowledge/extract_cards.py validate CARD-NNNN` until clean, then
     `python3 tools/knowledge/extract_cards.py coverage CARD-NNNN` and write `net_new`.
   - Record the decision: `python3 tools/knowledge/extract_cards.py mark --thread <channel_id>:<thread_ts> --status carded --card CARD-NNNN`
     or `--status skipped --reason "..."`.
   - Optional: `python3 tools/knowledge/review.py import-lessons --vault <team vault> [--since YYYY-MM-DD]`
     scaffolds cards from the vault Lessons file without editing it.
6. **Queue.** `python3 tools/knowledge/review.py queue` renders `review-queue.md` in the
   store. A human ticks `[x]`: the agency lead any card, the ads lead ads cards, the
   operations lead logistics, catalog, support-cases and account-health cards. The agency
   lead decides every `policy_risk` or `publishable=false` card.
7. **Promote ticked cards.** `python3 tools/knowledge/review.py promote --card CARD-NNNN --ticked-by <agency-lead|ads-lead|operations-lead>`
   runs `tools/knowledge/new_unit.py`, `tools/knowledge/build_knowledge_index.py --readme`
   and `tools/knowledge/lint_knowledge.py --strict`, and prints the unit path. A lint
   failure removes the unit again and leaves the card in `candidate/`. Reject with
   `python3 tools/knowledge/review.py reject --card CARD-NNNN --reason "..."`. Units enter as
   draft and unverified; never set `reviewed` or `verified` yourself.
8. **Ledger.** With the operator's go-ahead in this session:
   `python3 tools/knowledge/ledger.py append --from-staging`, then
   `python3 tools/knowledge/ledger.py check`.
9. **Run note.** `python3 tools/knowledge/review.py run-note --date YYYY-MM-DD --vault <team vault>`
   writes `Runs/YYYY-MM-DD-knowledge-sweep.md` in the vault.
10. **Report and stop.** Units promoted with ids and paths, cards rejected, candidates still
    open per topic, the lint result, and the windows still missing or partial.

Stop rules: never commit or push; never post, react or send in Slack or anywhere else; no
vault write except the ledger append and the run note, and both only in an attended
session (they refuse when `WIZARDS_AI_MODE=1`); nothing client-specific enters
`knowledge/`; never hand-edit a capture library or the Lessons file.
