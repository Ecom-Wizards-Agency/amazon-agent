# Cross-agent handoff

One file, self-contained. The operator pastes a path, the next agent reads that file and
nothing else, and continues. If the receiving agent has to ask a question the file should have
answered, the handoff failed.

This is the only handoff format. It replaces the personal-vault copies that drifted from it.

## The rule

An agent that stops mid-task, when another agent may continue, writes one of these before it
stops. Do not make the operator translate between Codex and Claude.

## Where the file goes

| Case | Path |
|---|---|
| Client has a team-vault folder | `<team-vault>/Clients/<Client>/Handoffs/YYYY-MM-DD-<topic>.md` |
| No vault folder for that client | `output/<client>/<workflow>/YYYY-MM-DD-<topic>-handoff.md` |
| Keyword-workbook runs | auto-generated: `build_keyword_workbook.py --config <cfg> --preflight` |

Never in a personal vault, and never a new client folder just to hold one. Resolve the vault
with `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`.

**No YAML frontmatter.** A handoff is transient work state, not vault knowledge, and `handoff`
is deliberately absent from the vault type vocabulary. The header lines below carry everything.

**One file per task, not per exchange.** A task that bounces Claude to Codex and back is still one
handoff file. The receiving agent rewrites it in place when it hands the task back: update the
header, replace sections 1 to 3 with what the next agent must now do, and fold what it just did
into section 4. The file is a baton, not a transcript.

That means a handoff is always current rather than a pile of stale instructions somebody has to
read in order. The record of what happened lives in the run note (`Clients/<Client>/Runs/`), which
is where a reader should look for history. If the handoff and the run note disagree, the run note
is the account of what happened and the handoff is only what to do next.

Open a new file only for a genuinely new task.

## The shape

Copy this. Keep the section order and the numbering.

```markdown
# Handoff: <one line, what this is>

Updated: DD.MM.YYYY
From: <Claude | Codex>
Next agent: <Codex | Claude | any>
Status: <ready | blocked on X>
Round: <1, 2, ... incremented each time the task changes hands>

## 1. Do this next

<The single next action, as an imperative. Exact command, exact absolute path, exact UI
target. If there are several steps, number them in the order they must happen. This is the
only section the next agent is guaranteed to read in full.>

## 2. Stop when

<The finish line, stated so it can be checked. Then: what to report, and to whom.>

## 3. Never

<Non-goals and risky actions, each one a line. Be concrete: "do not run the builder",
not "be careful". Include anything already tried that must not be retried.>

## 4. State: what is already true

<Verified facts only, each with how it was verified. An unverified assumption goes in
section 7, never here. This is what stops the next agent redoing finished work.>

## 5. Inputs

| What | Where |
|---|---|
| <file, export, screenshot, workbook> | <absolute path or Drive/Doc link> |

## 6. Context that cannot be inferred

<Account, marketplace, brand, ASINs, niche IDs, filters, date ranges. Decisions already
made and the reason, so they are not silently reversed. Anything the operator said that
changed the task.>

## 7. Caveats

<Missing data, conflicting data, tool limits, unsafe claims, anything provisional. If a
number in section 4 is a floor or an estimate, say so here.>
```

## Why this order

The next agent reads top-down and its context may be truncated from the bottom, so the file is
ordered by what breaks if it is missed. The action first, because that is the point of the file.
Guardrails second, because a wrong action is more expensive than a slow one. Facts and paths
next. Caveats last, because they qualify the work rather than direct it.

Two sections earn their place by having failed in practice. **Section 4** is what stops an agent
redoing a finished step, so a fact belongs there only with the check that proved it. **Section 3**
is where "already tried, does not work" goes, which is the single thing most often lost in a
handoff and most expensive to rediscover.

Write absolute paths. The next agent may start in a different working directory, and a relative
path that resolved for you is a path that silently resolves somewhere else for it.
