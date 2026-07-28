---
type: reference
date: 2026-07-26
status: active
tags: [scripts, transcription, video-notes, tooling]
---

Tooling for turning YouTube videos into timestamped transcripts, built for the [[amazon-ads-claude-video-watchlist]] run. Mirrored into the Amazon Agent repo at `tools/video-transcription/`.

## Why this exists rather than the `watch` skill

The `watch` skill always prefers YouTube's auto-captions when they exist and has no force-Whisper flag. Those captions are unusable for this corpus: they mangle the domain vocabulary (`asens` for ASINs, `a cost` for ACOS, `clawed` for Claude, `rorowaz` for ROAS, `PBC` for PPC) and arrive in a rolling window that repeats every line: **427 words/min vs Whisper's 187, i.e. 2.3× the tokens for identical content.** These scripts bypass the caption path entirely.

## Files

| File | Purpose |
|---|---|
| `transcribe.py` | Audio-only download → chunk → transcribe → timestamped markdown on stdout |
| `fixterms.py` | Repairs whisper-1's systematic Amazon-jargon errors, corpus-wide |
| `worker.sh` | Single-video wrapper for `xargs -P N` parallel runs; skips completed, cleans audio |
| `worker_diarize.sh` | Same wrapper against the `diarize` backend |

```bash
python3 transcribe.py --out DIR -- VIDEO_ID          # note the --, see gotchas
python3 transcribe.py --backend diarize --out DIR -- VIDEO_ID
python3 fixterms.py DIR            # dry run
python3 fixterms.py DIR --apply

export VT_WORKDIR=/path/to/run            # transcripts land in $VT_WORKDIR/wh and /di
xargs -P 4 -n 1 ./worker.sh < queue.txt
xargs -P 4 -n 1 ./worker_diarize.sh < queue.txt

VT_SUBDIR=ls xargs -P 6 -n 1 ./worker.sh < livestreams.txt   # same worker, own folder
```

Both workers find `transcribe.py` next to themselves, so they run from anywhere. `VT_WORKDIR` is the only thing they need told, and it defaults to the current directory. Keep it outside the repo: transcripts are run output, not source. `VT_SUBDIR` overrides the output folder (`wh` / `di`), so a second batch that needs its own directory is an env var rather than a copied script.

**A transcript with no segments is a FAILURE, not a result.** `transcribe.py` can exit 0 having produced no timestamped lines. The workers check the artifact rather than the exit code: an empty result is reported as `EMPTY <id>`, exits non-zero, and is never saved. The completed-work skip applies the same test, so an empty file already on disk is retried instead of being skipped forever, which is how a video can silently never get transcribed across every rerun.

Credentials are read from `~/.config/watch/.env` (`OPENAI_API_KEY`, `GROQ_API_KEY`). Never hardcoded, never logged.

## Backends

| `--backend` | Model | Timestamps | Speakers | Cost |
|---|---|---|---|---|
| `openai` (default) | `whisper-1` | ✅ | ❌ | $0.006/min |
| `diarize` | `gpt-4o-transcribe-diarize` | ✅ | ✅ A/B/C | unpublished, ~3× |
| `groq` | `whisper-large-v3` | ✅ | ❌ | free tier |

`gpt-4o-transcribe` is deliberately absent: it is the most accurate on jargon but **returns no timestamps at all**. It accepts `verbose_json` and `timestamp_granularities[]` and silently ignores both.

## Hard-won gotchas

> [!warning] These cost hours to find. Read before changing anything.
> - **Upload size, not network flakiness.** The API drops the connection (`RemoteDisconnected`) far below its documented 25 MB cap. Every video over ~19 min failed; every one under ~13 min succeeded. Chunking is set to 10 min / ~4.8 MB. ==Retry logic does not help. The failure is deterministic, so retries just fail slower.==
> - **Diarize needs its own, smaller chunks** (240 s / 1.5 MB) and requires `chunking_strategy` or it 400s.
> - **Video IDs beginning with `-`** (e.g. `-3LbXP57BVs`) parse as CLI flags. Always pass `-- "$id"`. Five such IDs exist in this queue. The same bug bites `grep *.md` when a file is named `-xxx.md`.
> - **zsh does not word-split unquoted variables** the way bash does. `for id in $IDS` runs once with the whole string.
> - **Auth success ≠ available quota.** A key can return 200 on `/v1/models` while having zero balance; `insufficient_quota` only appears on a real billable call. Test with an actual transcription.
> - **Clean up audio on failure, not just success.** Orphaned working dirs reached 1.8 GB in one run.

## Known transcription errors

`fixterms.py` repairs these, each verified against `gpt-4o-transcribe` on identical audio, not guessed:

| Heard as | Actually | Frequency |
|---|---|---|
| "a cost" | ACOS | 140, ==wrong more often than right== (153 mangled vs 132 correct) |
| "PBC" | PPC | 64 |
| "tacos" | TACOS | 11, only with metric context on the line |

Guards preserve real English: `a cost of` and `a cost per` are left alone (8 legitimate cases in the corpus), and bare "tacos" is only changed when the line also mentions ACOS, ad spend, revenue, margin, or a percentage.

## Open issue

> [!question] Diarize unreliable as of 2026-07-26
> `gpt-4o-transcribe-diarize` worked on short slices (100 s, 180 s) and correctly separated three speakers, then began returning `HTTP 000` (connection dropped) on every file including ones that had just succeeded, while `whisper-1` returned 200 on the same file at the same moment. Cause unconfirmed: possibly a per-model rate limit, possibly capacity. **Retest before relying on it.**

Output convention and corpus: [[Intelligence/video-notes/_transcripts/_index]].
