---
name: gauntlet-loop
description: Use when running a Gauntlet Loop — driving work to a high quality bar by splitting it into independently judgeable pieces, building each with one agent, and judging each with a separate blind critic against a concrete external reference, looping until the reference stops winning. Covers agentic capabilities, reinforcement learning, and general coding. Loaded by every /gauntlet:* command.
---

# Gauntlet Loop

The method is Matt Shumer's (<https://somethingbig.ai/gauntlet-loop>). This skill is the operational
contract for running it inside Claude Code with real enforcement instead of good intentions.

## The whole idea

> Give a lead agent a goal and a real example of what great looks like. The lead decides how to break
> the goal into the smallest pieces that can be improved separately. Each piece gets its own builder
> and a separate critic with fresh context. The builder makes something. The critic compares it
> against the reference. If the reference wins, the critic names the biggest remaining gap and sends
> it back. Then another round begins.

Ordinary agent work stops at "pretty good" because the agent that built the thing is the one deciding
it is done. The Gauntlet Loop removes that decision from the builder and hands it to an external
standard.

## The six rules

1. **Goal, not implementation.** State the destination. Do not prescribe architecture, decomposition,
   or a round count. Strong models pick better routes than your outline does.
2. **A real bar.** "Make it amazing" is not a bar. The bar is a concrete artifact or measurement a
   critic can *inspect*: reference screenshots, a held-out task suite, a baseline learning curve, a
   reference implementation, a latency budget. It does not have to be reachable — it has to point.
3. **The lead splits the work.** Smallest pieces that can be improved and judged *separately*. Not
   "make the agent better" — "make this recovery-from-tool-error path beat the reference trajectory."
4. **The builder never grades itself.** Separate agent, fresh context, no builder rationale, blind
   A/B where possible. The builder remembers why every choice was reasonable; you do not want
   reasonable, you want an independent judgment.
5. **Keep going.** No arbitrary final round. Stop when you like it, when gaps stop mattering, or when
   the compute budget runs out — not at round three.
6. **Watch without interrupting.** A live board that updates itself, so you never have to break the
   run to ask how it is going.

Optional: after each wave, one fresh **smoother** inspects the whole artifact and reconciles the
independently-improved pieces so the result feels like one thing.

## What this plugin enforces mechanically

Rules 2 and 4 fail silently when they are only prompt text, so they are wired into scripts:

| Rule | Enforcement |
|---|---|
| No loop without a bar | `ab.py stage` refuses to stage a trial unless `.gauntlet/bar.md` exists and records a PASS on all five soundness checks |
| Critic is blind | `ab.py stage` shuffles candidate and reference into `A/` and `B/` under a per-trial random assignment; the mapping is written **outside** the trial directory to `.gauntlet/keys/`, mode 0600 |
| Critic stays blind | A `PreToolUse` hook denies any tool call whose input path touches `.gauntlet/keys/` — the mapping is unreadable during judging, by any agent |
| Critic sees artifacts, not arguments | The staged trial directory contains only `A/`, `B/`, and a `brief.md` generated from the goal and bar. Builder notes, diffs, and rationale are never copied in |
| No re-grading until you like the answer | `ab.py verdict` refuses to overwrite an existing verdict for a trial |
| Verdicts are receipts | Every staged file is sha256'd into `.gauntlet/ledger.jsonl` alongside the verdict and the revealed mapping |

Nothing here constrains *what* the lead builds or *how* it splits the work. Determinism lives in the
gate, never in the generation.

## The bar-soundness gate

A bar earns the loop only if all five hold. `/gauntlet:bar` produces `.gauntlet/bar.md` with an
explicit verdict per check and the evidence for it.

1. **Inspectable** — the critic can open, run, or measure the bar directly. A description of a good
   outcome is not a bar; the outcome is.
2. **External** — not authored by the builder and not derived from builder output. If the builder
   wrote the test, the test is a mirror.
3. **Held-out** — the builder cannot see, train on, or tune against the exact instances used to
   judge. Name the split and how it is enforced.
4. **Discriminating** — the current output *loses* to it right now. If round 0 already wins, the bar
   is too low; raise it before starting.
5. **Un-gameable** — name the cheapest way to satisfy the bar without doing the work. If a cheat
   exists, add the counter-check that kills it, and record both.

When you do not know the right bar, finding one is the first piece of work — dispatch
`gauntlet:bar-scout`. Do not let the agent invent its own definition of "good"; make it find a
comparison that already exists in the world.

## Loop shape

```
/gauntlet:new  →  goal + domain          →  .gauntlet/charter.md
       ↓
/gauntlet:bar  →  bar-scout + 5 checks   →  .gauntlet/bar.md         (blocks the loop until PASS)
       ↓
/gauntlet:run  →  lead decomposes        →  .gauntlet/pieces.json
       ↓
       wave:  for each piece, in parallel
              builder  → artifact
              ab.py stage --ref <bar> --cand <artifact>
              critic   → inspects A and B blind → ab.py verdict
              ab.py reveal → WIN | LOSS | TIE + biggest gap → ledger
              LOSS/TIE → gap goes back to that piece's builder → next round
       ↓
       smoother (optional, end of wave) → coherence pass over the whole artifact
       ↓
       next wave — no fixed round count
       ↓
/gauntlet:status  →  board.py render → .gauntlet/board.html (auto-refreshing)
```

## Working directory layout

```
.gauntlet/
  charter.md          goal, domain, constraints, stop condition
  bar.md              the bar + five soundness verdicts + counter-checks
  pieces.json         lead's decomposition (its own; never pre-supplied)
  ledger.jsonl        append-only receipts: staged / verdict / resolved
  ab/<trial>/         A/  B/  brief.md  verdict.json
  keys/<trial>.json   the A/B mapping — hook-denied to all agents
  board.html          live progress page
  work/<piece>/       builder scratch, notes, drafts (never staged to a critic)
```

## Roles

- **lead** (`gauntlet:lead`) — owns decomposition, wave scheduling, reveal, and the board. Never
  builds and never judges.
- **builder** (`gauntlet:builder`) — one per piece. Sees the goal, the bar, and the last gap. Fresh
  context per piece, carried across rounds of that piece only.
- **critic** (`gauntlet:critic`) — one per trial. Fresh context every trial. Sees `A/`, `B/`, and the
  brief. Never sees which is which, who made either, or any prior verdict.
- **bar-scout** (`gauntlet:bar-scout`) — finds candidate bars and runs the five checks.
- **smoother** (`gauntlet:smoother`) — end-of-wave coherence pass. Reconciles; does not redesign.

## Domain bar recipes

Read the one that matches before scouting a bar. Each covers what to judge, which bars are real in
that domain, the leakage traps that make a bar fake, and how to decompose.

- `references/bars-agentic.md` — agentic capabilities: tool use, recovery, planning, stopping
- `references/bars-rl.md` — reinforcement learning: returns, curves, seeds, eval protocol
- `references/bars-coding.md` — general coding: differential testing, reference impls, budgets

## Stopping

There is no completion criterion in the loop. You stop it. Record the reason in `charter.md` —
"gaps stopped mattering", "budget", "shipped" — because a run with no recorded stop reason tends to
get restarted for no reason.
