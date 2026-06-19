# Stargraph Provenance-Typed Facts

Every fact asserted in a Stargraph run carries provenance metadata. Rules can
pattern-match on it, audit can reconstruct it, and replay can filter on it.
Provenance is non-negotiable — a run without a complete trace is treated as an
error, not a warning.

## The Envelope

Tools and nodes attach a `__stargraph_provenance__` envelope to their outputs:

```json
{
  "...": "output fields",
  "__stargraph_provenance__": {
    "origin": "tool",
    "source": "nautilus",
    "external_id": "<broker request_id>"
  }
}
```

| Field | Type | Meaning |
|---|---|---|
| `origin` | string | Where the value came from (see Origin Values). |
| `source` | string | Specific emitter — node name, tool name, rule name, subsystem. |
| `external_id` | string | Optional id correlating to the external system that produced it. |

When the envelope is folded into the fact store, the fact additionally carries
run-scoped metadata — `run_id`, `step`, `confidence`, and a `timestamp` — which
the runtime stamps automatically. Nodes and rules cannot forge them.

## Origin Values

The documented origin values are:

| `origin` | Emitted when | Meaning |
|---|---|---|
| `tool` | A tool call returns structured data. | High trust if the tool itself is trusted. |
| `llm` | An LLM-backed node (DSPy module, raw chat) emits a value derived from model output. | Treat as plausibly-true; verify before acting. |
| `rule` | A Fathom/CLIPS rule asserts a derived fact in its RHS. | Symbolic derivation from premises. |
| `system` | The runtime or a subsystem (e.g. trigger / scheduler / audit sink) emits the fact. | Runtime-attested. |

## Pattern Matching on Provenance

Rules can constrain on any provenance field. Examples:

Only act on tool-origin facts with confidence at least 0.8:

```clips
(defrule act-on-trusted-tool-output
  (citation (url ?u)
            (origin tool)
            (confidence ?c&:(>= ?c 0.8)))
  =>
  (assert (next-node synthesize)))
```

Prefer rule-derived facts over raw LLM output for the same key:

```clips
(defrule prefer-rule-over-llm
  ?bad <- (label (key ?k) (origin llm))
  (label (key ?k) (origin rule))
  =>
  (retract ?bad))
```

Halt if a system-origin fact contradicts an LLM-origin one:

```clips
(defrule system-overrides-llm
  (claim (subject ?s) (value ?v1) (origin system))
  (claim (subject ?s) (value ?v2&~?v1) (origin llm))
  =>
  (assert (control halt))
  (assert (audit (reason "system contradicts llm") (subject ?s))))
```

## Confidence Convention

`confidence` is a float in `[0, 1]`. Calibration varies by origin:

- `tool` — the tool's own confidence if it returns one; else 1.0 for
  deterministic tools, normalized retrieval scores for lookups.
- `llm` — logprob-derived confidence when available; otherwise a documented
  default unless the prompt asks the model for a self-reported score.
- `rule` — `min` of premise confidences by default; rules may override with an
  explicit aggregation.
- `system` — runtime-attested events are typically pinned at 1.0.

Sources should document their calibration in their skill or pack README.

## What replay captures

Every run emits a trace sufficient to replay it: the IR hash, the plugin set
(distribution name, version, `api_version` per plugin), the Fathom decision log
(rule firings in order with fact snapshots), and content-addressed I/O envelopes
for all node inputs and outputs. Facts are indexed by `run_id` and `step`; the
fact log is persisted by the configured `FactStore` provider.

## Inspecting facts

There is no `facts` subcommand. Inspect a run's facts and state over a SQLite
checkpointer DB with `stargraph inspect`:

```bash
# CLIPS facts asserted/retracted between step 5 and step 9
stargraph inspect <RUN_ID> --db .stargraph/run.sqlite --diff 5 9

# state snapshot at step 7
stargraph inspect <RUN_ID> --db .stargraph/run.sqlite --step 7

# timeline (enriched with an audit log)
stargraph inspect <RUN_ID> --db .stargraph/run.sqlite --log-file run.jsonl
```

The fact-diff view (`--diff N M`) prints the CLIPS fact delta between two steps;
the state view (`--step N`) prints the IR-canonical state dict at that step.
