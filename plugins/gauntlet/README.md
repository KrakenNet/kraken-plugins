# gauntlet

A Gauntlet Loop harness for Claude Code.

The method is Matt Shumer's, from [How to Run a Gauntlet
Loop](https://somethingbig.ai/gauntlet-loop) — the prompting approach behind
[Claude of Duty](https://github.com/mshumer/Claude-of-Duty). This plugin turns it into a repeatable
harness with the two load-bearing rules enforced by scripts instead of by hope.

## The idea

Give a lead agent a goal and a real example of what great looks like. It splits the goal into the
smallest pieces that can be improved separately. Each piece gets a builder and a **separate** critic
with fresh context. The critic compares the work against the reference blind; when the reference
wins, it names the biggest gap and sends the work back. Repeat until you stop it.

Agent output plateaus at "pretty good" because the agent that built the thing decides it is done.
The loop takes that decision away and gives it to something external.

## What is enforced, not just asked for

| Rule | Mechanism |
|---|---|
| No loop without a bar | `ab.py stage` refuses unless `.gauntlet/bar.md` shows PASS on all five soundness checks |
| The critic is blind | Candidate and reference are shuffled into `A/` and `B/`; the mapping is written outside the trial dir, mode 0600 |
| The critic stays blind | A `PreToolUse` hook denies any tool call that touches `.gauntlet/keys/` |
| The critic sees artifacts, not arguments | Staged trials contain only `A/`, `B/`, and a generated brief — no builder notes, diffs, or rationale |
| No re-grading | `ab.py verdict` refuses to overwrite an existing verdict |
| Verdicts are receipts | Every staged file is sha256'd into an append-only `ledger.jsonl` |

Nothing constrains what the lead builds or how it splits the work. The determinism is in the gate,
never in the generation.

## Commands

| Command | Does |
|---|---|
| `/gauntlet:new "<goal>"` | Capture the goal + domain, write the charter |
| `/gauntlet:bar` | Find a real bar, run the five soundness checks, gate the loop |
| `/gauntlet:run` | Decompose, then run waves of build → blind critique → revise |
| `/gauntlet:status` | Ledger, open gaps, live board |

## Agents

`gauntlet:lead` · `gauntlet:builder` · `gauntlet:critic` · `gauntlet:bar-scout` · `gauntlet:smoother`

## Domain recipes

The bar is the hard part, and it is domain-specific. Each recipe covers what to judge, which bars are
real, the leakage traps that make one fake, and how to decompose:

- `references/bars-agentic.md` — tool use, recovery, planning, stopping. Verifier leakage,
  task memorisation, pass@1 vs best-of-n, harness cheating, cost blindness.
- `references/bars-rl.md` — returns, curves, seeds, eval protocol. Protocol drift, seed
  cherry-picking, tuning on eval, shaped-reward inflation, held-out levels.
- `references/bars-coding.md` — differential testing, reference impls, property tests, perf
  budgets. Builder-written tests, test mutation, overfit fixtures, mock leakage.

These are recipes for *finding* a bar, not menus of preset bars. `gauntlet:bar-scout` searches for
one that already exists in the world and proves it holds up.

## Loop

```
/gauntlet:new  → charter.md
/gauntlet:bar  → bar.md            ← blocks the loop until all five checks PASS
/gauntlet:run  → pieces.json
      wave:  builder → ab.py stage → blind critic → ab.py reveal → gap → next round
             smoother (end of wave)
/gauntlet:status → board.html      ← auto-refreshing, phone-friendly
```

## Scripts

```bash
ab.py stage --piece <id> --round <n> --cand <ours> --ref <bar> --goal-file .gauntlet/charter.md
ab.py verdict <trial> --winner A|B --gap "<the biggest gap>"     # run by the critic
ab.py reveal <trial>                                             # run by the lead
ab.py ledger [--json]
board.py render | serve [--port 8787] [--host 0.0.0.0]   # localhost by default; keys/ is never served
```

`GAUNTLET_ROOT` overrides `.gauntlet/`.

## Stopping

The loop has no completion criterion — that is the design. You stop it when the result is good
enough, when gaps stop mattering, or when the budget runs out. If every piece has been winning for
several waves, the bar went soft: `/gauntlet:bar --recheck`.

## Credit

Method: [Matt Shumer](https://x.com/mattshumer_) — <https://somethingbig.ai/gauntlet-loop>.
This plugin is an independent implementation of the published method.
