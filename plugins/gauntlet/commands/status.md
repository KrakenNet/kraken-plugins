---
description: Show Gauntlet Loop state — per-piece round history, win/loss against the bar, open gaps, trials awaiting a verdict. Renders the live board.
argument-hint: [--json] [--serve [port]]
allowed-tools: [Bash, Read, Glob, Grep]
---

# /gauntlet:status

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ab.py ledger
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py render
```

`--json` → `ab.py ledger --json` for the raw receipt trail.
`--serve [port]` → `board.py serve --port <n>` (default 8787, localhost). Add `--host 0.0.0.0`
only if the user asks to reach it from another device, and say so when you do.

## Reading it

- **LOSS / TIE** — the bar still wins; that piece's gap is open and belongs back with its builder.
- **WIN** — that piece beat the bar this round. Several wins running across most pieces means the bar
  has gone soft, not that the work is done. Run `/gauntlet:bar --recheck` and say so plainly.
- **JUDGING** — staged, no verdict yet. A trial stuck here means a critic died or never ran; the lead
  should dispatch a fresh one against the same trial directory.

Report the state and the open gaps. Do not editorialise about whether the run should stop — that call
is the user's, and a loop that talks itself into stopping is the failure this method exists to fix.
