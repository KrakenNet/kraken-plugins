# Bars for agentic capabilities

Building an agent that uses tools, recovers from failure, plans, and knows when to stop.

## What actually gets judged

Not the prompt. Not the scaffold diff. **The trajectory and the end state.** An agent is a policy over
a messy environment, so the artifact a critic inspects is:

- the full transcript — every tool call, every result, every recovery
- the final environment state — the repo, the filesystem, the database, the API side effects
- the outcome, checked programmatically by something the agent did not write

Judging the prompt is how you end up with an agent that reads beautifully and fails on contact.

## Bars that are real

Ranked roughly by strength.

1. **A held-out task suite with programmatic outcome checks.** The strongest bar available. Tasks the
   builder has never seen, graded by an assertion the builder did not author — tests that already
   existed, a schema, an idempotent state check, a diff against known-good output. SWE-bench-style
   instance sets, real closed tickets from your own tracker, real support transcripts with known
   resolutions.
2. **Expert reference trajectories.** A human — or a strong agent under a different scaffold — solving
   the same task. The critic compares trajectory against trajectory blind: which one recovered
   better, which wasted fewer steps, which noticed the wrong turn earlier. Excellent for judging
   *process* qualities that outcome checks are blind to.
3. **A stronger competing agent on identical instances.** Same tasks, same budget, same tools. Cheap
   to obtain, and it moves as the field moves, which keeps it from going soft.
4. **Production incident replays.** Real failures your agent should have handled, replayed from
   captured state. Unbeatable for realism, limited in supply — spend them carefully and hold some
   back.

## Traps that make an agentic bar fake

- **Task memorisation.** Public benchmarks are in pretraining data. A high score can mean the model
  recognises the instance, not that your scaffold works. Mitigate with private instances, freshly
  captured tasks, or perturbed variants — and treat public-benchmark deltas as weak evidence.
- **Verifier leakage.** The agent writes, edits, or can read the check that grades it. This is the
  single most common way an agentic loop deceives itself. The grader lives outside the agent's write
  scope, and ideally outside its read scope.
- **Single-seed flake.** Agents are stochastic; one run tells you almost nothing. Run n≥5 per task.
  Report **pass@1 and the pass rate**, never best-of-n — best-of-n measures your sampling budget, not
  your agent. A "regression" inside seed variance is noise, and chasing it burns rounds.
- **Harness-level cheating.** Editing the tests, `git checkout`-ing the solution, curling the answer,
  writing to the grading path, catching-and-passing. Sandbox the run, snapshot the grader, diff the
  environment for out-of-scope writes. Pair this with forge's anti-cheat scan on any diff the agent
  produced.
- **Cost blindness.** An agent that wins by burning 40x the tokens has not won. Put tokens, wall-clock,
  and tool-call count in the comparison, or the loop will optimise straight into brute force.
- **Reward hacking through side effects.** Task passes; the agent also deleted a table. Judge the end
  state, not just the assertion.

## Decomposition axes

Pieces a lead can hand to independent builders and critics:

- **Tool selection** — right tool, first try, versus flailing across the toolbelt
- **Failure recovery** — malformed payload, timeout, auth expiry, rate limit, partial write
- **Context management** — what it keeps, what it drops, what it re-reads, behaviour near the limit
- **Planning granularity** — decomposition quality on long-horizon tasks
- **Stopping** — knowing it is done; knowing it is stuck; not declaring victory on a red test
- **Cost per solve** — tokens and calls at fixed quality
- **Verification behaviour** — does it check its own work before claiming completion

Each of those loses to a reference trajectory in a specific, nameable way. That is what makes them
good pieces.

## Enforcing held-out

Pin instances by content hash. Keep a rotating unseen split the builder never touches — a split the
builder has read once is spent, permanently. Record which instances a run consumed in the ledger, and
retire them.
