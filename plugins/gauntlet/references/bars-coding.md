# Bars for general coding

Building or improving software where correctness, performance, and robustness are the point.

## What actually gets judged

**Running behaviour.** Executed tests, measured latency, real output on real inputs, the actual
rendered page. Not "the code looks clean", not a description of the design, not the builder's account
of what it handles.

## Bars that are real

1. **A reference implementation, run side by side.** A well-regarded library that already solves this.
   Feed both the same inputs and diff the outputs — **differential testing**. This is the strongest
   coding bar there is, and it happens to be a literal blind A/B: the critic sees two output sets and
   picks the one that is right, without knowing which came from where.
2. **A pre-existing test suite the builder did not write.** Upstream tests, tests from the ticket,
   tests written by a separate agent that never sees the implementation. If the builder wrote the
   test, the test is a mirror.
3. **Property-based tests over an oracle.** Hypothesis/QuickCheck-style invariants: round-trips,
   idempotence, algebraic laws, agreement with a slow-but-obviously-correct implementation. Finds the
   inputs nobody thought to write down.
4. **A performance budget on fixed hardware and a fixed workload.** p50/p95/p99 latency, throughput,
   memory ceiling, allocation count. Concrete and inspectable — but only if the workload is pinned
   and the machine is quiet.
5. **A real bug corpus.** Historical bugs from this codebase, replayed. Does the new implementation
   still fall for them?
6. **A security review checklist against a real standard.** OWASP, a threat model, `semgrep` rules
   the builder did not author.

## Traps that make a coding bar fake

- **Builder-written tests.** Generator and evaluator collapse into one agent and the loop measures
  self-consistency. If the builder must write tests, a *separate* agent that never sees the
  implementation writes the ones that judge it.
- **Test mutation.** Assertions loosened, cases deleted, `skip`/`xfail`/`@pytest.mark.skip` added,
  tolerances widened. Judge tests as diffed-against-baseline, not as they currently stand. A round
  where the test file changed and the source did not is a red flag, not a pass.
- **Hardcoded expected values.** The function returns the fixture. Differential testing on fresh
  inputs kills this instantly; a fixed fixture set never will.
- **Overfit to fixture data.** Passes on the ten known inputs, breaks on the eleventh. Property-based
  tests and fresh generated inputs are the counter.
- **Mock leakage.** The mock is in the production path, so the test proves the mock works.
- **Green by absence.** The suite passes because it no longer runs the hard case. Track test *count*
  and coverage of the changed lines alongside pass rate.
- **Benchmark noise.** Unpinned CPU, thermal throttle, a noisy laptop, one run. Fixed workload,
  multiple runs, report the distribution — a 5% "win" on one run is nothing.
- **"Clean code" as a bar.** Not inspectable, not discriminating, infinitely arguable. Readability is
  real, but judge it against *specific reference code* the critic reads blind alongside ours, never
  against an adjective.

## Decomposition axes

- **Per module or per public interface** — each judged against the reference's equivalent
- **Per invariant** — one property, one builder, one critic
- **Per endpoint** — contract conformance, error taxonomy, status codes
- **Error handling and edge behaviour** — usually the entire real gap against a mature reference
- **Performance** — separate piece, separate bar, separate critic; do not let it ride along with
  correctness or it will be traded away silently
- **API ergonomics** — judged blind against the reference library's call sites, not against taste

## Complements in this marketplace

- `forge` — spec-anchored pipeline with locked tests and an anti-cheat gate. Its anti-cheat scan is
  the right PostToolUse companion to a coding gauntlet: it catches stubs, `NotImplementedError`,
  skipped tests, and demo data before a critic wastes a round on them.
- `ui-fidelity` — for UI work, its gates are a ready-made hard bar (dead buttons, orphan routes,
  flow-continuity, contrast). Machine-checkable, external to the builder, and not gameable by prose.

## Enforcing held-out

Keep a fresh-input generator rather than a fixed fixture set. Keep the judging tests in a path the
builder cannot write. Run differential comparisons on inputs generated *after* the builder finished
the round.
