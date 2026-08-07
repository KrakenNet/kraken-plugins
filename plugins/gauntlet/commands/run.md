---
description: Run the Gauntlet Loop — lead decomposes the goal, each piece gets a builder and a separate blind critic, losing rounds go back to the builder, and the loop keeps going until you stop it.
argument-hint: [--waves <n>] [--pieces <n>] [--no-smoothing] [--resume]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, Agent, TodoWrite]
---

# /gauntlet:run

Read `${CLAUDE_PLUGIN_ROOT}/skills/gauntlet-loop/SKILL.md`.

## Preconditions

```bash
test -f .gauntlet/charter.md || echo "no charter — run /gauntlet:new"
test -f .gauntlet/bar.md     || echo "no bar — run /gauntlet:bar"
```

Both required. `ab.py stage` enforces the bar independently, so do not try to route around it.

## Dispatch the lead

```
Agent({
  subagent_type: "gauntlet:lead",
  prompt: "Read .gauntlet/charter.md and .gauntlet/bar.md.
           Decompose the goal into the smallest pieces that can be improved and judged separately —
           your call, write .gauntlet/pieces.json.
           Then run waves: per piece, dispatch gauntlet:builder, stage a blind trial with ab.py,
           dispatch a FRESH gauntlet:critic with only the trial dir, reveal, feed the gap back.
           Render the board after every reveal. Keep looping — no fixed round count.
           <--waves n: run n waves then report and pause>
           <--no-smoothing: skip the end-of-wave smoother>"
})
```

`--resume` — read `.gauntlet/pieces.json` and the ledger, and continue from the current round of
each piece instead of decomposing again.

`--pieces <n>` — a soft ceiling on parallel pieces when compute is tight. It is a budget hint, not a
decomposition instruction; the lead still decides what the pieces *are*.

## While it runs

Point the user at the board rather than at the transcript:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py serve --port 8787
```

Open `http://localhost:8787/board.html` — it refreshes itself. That is the point: you watch without
interrupting.

To read it from a phone, add `--host 0.0.0.0` and use the machine's LAN address. Tell the user that
binds to every interface before you do it. The server refuses to serve `keys/` on any host, so the
A/B mappings stay sealed either way.

## Stopping

The loop has no natural end. Stop it when the result is good enough, when gaps stop mattering, or
when the budget runs out — then record the reason in `.gauntlet/charter.md`.

Do not report the work as finished because a wave completed. Report state, and keep going.
