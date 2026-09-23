# Bars for reinforcement learning

Building a policy, a reward, an exploration strategy, or the training stack around them.

## What actually gets judged

**Evaluation rollouts under a frozen protocol the builder cannot modify.** Not the training curve the
builder screenshotted — training return is a diagnostic, not a result. The critic inspects:

- eval returns across seeds, under a fixed protocol (episode count, determinism, wrappers)
- the learning curve as a function of a stated budget (env steps or wall-clock — say which)
- rollout videos or state traces, when behaviour quality matters beyond scalar return
- sample efficiency and stability, not just the final number

## Bars that are real

1. **A published baseline on the same environment and budget.** Stable-Baselines3, CleanRL, or the
   original paper's reported numbers. Strong because the protocol is documented and someone else set
   the number. Reproduce the baseline yourself before trusting it — reported numbers drift from
   runnable ones.
2. **An expert or human demonstration return.** Where demos exist, expert return is a bar with real
   meaning, and the gap to it is interpretable.
3. **A scripted or classical controller.** PID, MPC, search, a hand-written heuristic. Frequently
   beats early RL, and losing to one is exactly the useful signal — it tells you the learned policy
   has not yet earned its complexity.
4. **An oracle / upper bound.** Optimal play, a solver, or a privileged-information policy. Never
   reachable, which is fine — it points, and it does not go soft.
5. **A frozen prior checkpoint of your own agent.** Weakest form, and the only one that is *internal*,
   so it fails the `external` check on its own. Use it as a regression guard alongside a real bar,
   never as the bar.

## Traps that make an RL bar fake

- **Protocol drift.** Deterministic versus stochastic eval, 10 versus 100 eval episodes, different
  action repeat, different frame stack, different reward clipping, different time limit. Any of these
  silently changes the number by more than your improvement. Freeze the eval protocol in a file, hash
  it, and refuse comparisons across a hash change.
- **Env version drift.** `gym` vs `gymnasium`, physics-engine and env-version bumps change achievable
  return. Pin the exact env id and library versions in the bar.
- **Seed cherry-picking.** The single most common fake result in the field. Use ≥5 seeds — 10 if you
  can afford it — and report **median and interquartile range**, or the IQM/stratified bootstrap CIs
  from Agarwal et al. 2021 ("Deep RL at the Edge of the Statistical Precipice"). Best-seed and
  max-over-training are both meaningless. A win inside the CI is not a win.
- **Tuning on the eval.** Hyperparameter search against the same seeds and env instances used to
  judge is the RL form of verifier leakage. Search on a train split of seeds/levels; judge on held-out
  ones.
- **Reward shaping that changes the task.** Shape and the number goes up because the task got easier.
  Judge on the *original, unshaped* return, always. Shaped return is a training-time device.
- **Budget confusion.** Sample efficiency and wall-clock efficiency are different claims. State which
  budget the bar fixes, and hold it fixed.
- **Eval-harness tampering.** The builder edits wrappers, normalisation, or the eval loop. Keep the
  eval harness in a path the builder cannot write, and have the critic run it — not the builder.
- **Evaluating on training levels.** For procedurally generated envs, generalisation is the whole
  question. Held-out level sets are not optional.

## Decomposition axes

- **Reward specification** — judged against the unshaped objective and against side effects
- **Exploration** — coverage and time-to-first-success, not just final return
- **Architecture / optimiser** — same budget, same protocol
- **Replay / rollout collection** — sample efficiency at fixed steps
- **Wrappers and normalisation** — a real source of "improvements" that are protocol changes
- **Eval harness itself** — a piece worth building first, and then freezing
- **Behaviour quality** — smoothness, safety, absence of degenerate exploits, judged from rollout
  video blind against the reference controller

## Enforcing held-out

Separate seed sets for train and judge. Separate level sets for procedural envs. Commit the eval
harness and its config hash, put it outside the builder's write scope, and record the hash in every
ledger entry so a protocol change invalidates the comparison instead of quietly winning it.
