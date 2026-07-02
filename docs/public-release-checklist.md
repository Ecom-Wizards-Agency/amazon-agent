# Public Release / Pre-Push Checklist

This repo is being prepared as a public-safe, reusable workspace. Run this checklist before **any commit that will be pushed to a public remote**. It is agent-neutral: whichever agent performs the push (Claude Code or Codex) and the operator both follow it. This file is itself public — keep real names, IDs, and client brands out of it.

## 1. Git identity (do not publish a personal machine identity)

The default git identity can fall back to a personal name plus the local machine hostname (e.g. `Name <user@SomeMacBook.local>`). Do **not** publish commits with that.

- Set a repo-local identity before committing:
  - `git config user.name "<public display name>"`
  - `git config user.email "<public or no-reply email>"`
- Check the branch history for an already-leaked identity before pushing:
  - `git log --format='%an <%ae>' | sort -u`
  - If personal identities already exist in commits that will be published, decide whether to rewrite history (`git rebase`/`filter-repo`) or start the public history from a squashed commit.
- End commit messages with the house co-author line (see the harness/commit convention).

## 2. No client or local data is staged

`.gitignore` already excludes `output/`, `_local/`, `_local-output/`, `evidence/`, `downloads/`, and client configs (`config.*.json`, keeping only `config.TEMPLATE.json`). Confirm it is working:

- `git status --porcelain` shows nothing under those folders and no `config.*.json` / `seo_content*` files.
- `git ls-files | grep -E 'output/|_local/|evidence/|downloads/'` returns only `.gitkeep` entries.

## 3. Public-safe content scan (staged + tracked files)

Sweep for anything that identifies the operator, a client, or internal infrastructure:

- **Operator/personal**: personal names, personal emails, personal absolute paths (`/Users/<name>`), private vault names, personal cloud-share links.
- **Client brand names**: cached help-library captures under `Amazon Seller Help/` and `Advertising Help After Login/` embed the logged-in account brand in each file's header — these still need a scripted scrub or re-capture and are a known outstanding blocker for a fully public repo. Do not assume markdown-only genericization covered them.
- **Internal IDs**: Notion database/data-source IDs, Slack channel IDs, MCP/chat session IDs, ads profile/team IDs.
- **Functional scripts**: `tools/*.py` may still carry personal paths or client-specific values — genericize or gitignore before publishing (do not change runtime behavior without testing).
- Representative sweep (adjust patterns to the current known-leaks list): grep tracked non-template files for personal name/email fragments, `/Users/[a-z]`, 32-hex ID strings, `api[_-]?key`, `token`, `secret`.

## 4. Secrets never ship

No API keys, tokens, cookies, bearer/refresh tokens, passwords, tax IDs, payment identifiers, or private keys anywhere in tracked files or history. Third-party API keys (e.g. the DataDive MCP key) live only in local MCP/client secret storage.

## 5. Branch → PR flow (how it goes online)

- Work on a branch; never commit straight to `main`.
- Open a PR to `main` and let the operator review the **full diff** before merge. Do not force-push shared branches. Do not push at all unless the operator has explicitly asked for this specific push.

## 6. Handoff to the pushing agent (e.g. Codex)

Because Codex holds the shared runtime for git work in the two-agent model, the push is often executed by Codex. Whoever hands off must give a copy-ready block containing: the exact branch, the files intended for the commit, confirmation that sections 1–4 passed (with the commands run), the target base branch for the PR, and any files deliberately left untracked. The pushing agent re-runs sections 1–4 before committing rather than trusting the handoff blindly.

## Change log of verified-safe additions

- 2026-07-02 — `skills/amazon-adlabs-audit/SKILL.md`, `.claude/commands/adlabs-audit.md`, and the `agent.md` routing edit scanned clean (no brand/PII/currency/ID leakage); brand-agnostic and ready to publish.
