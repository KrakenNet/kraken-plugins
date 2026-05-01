# Harbor Provenance-Typed Facts

Every fact asserted in a Harbor run carries provenance metadata. Rules can pattern-match on it, audit can reconstruct it, and replay can filter on it.

## The Tuple

Every fact carries:

```
(origin, source, run_id, step, confidence, timestamp)
```

| Field | Type | Meaning |
|---|---|---|
| `origin` | symbol | Where the fact came from (see Origin Values). |
| `source` | string | Specific emitter — node name, tool name, rule name, user id. |
| `run_id` | string | The run that produced the fact. |
| `step` | int | Monotonic step counter within the run. |
| `confidence` | float | In [0, 1]. See Confidence Convention. |
| `timestamp` | datetime | UTC, ISO-8601. |

The runtime stamps these automatically; nodes and rules cannot forge them.

## Origin Values

| `origin` | Emitted when | Meaning |
|---|---|---|
| `llm` | An LLM-backed node (DSPy module, raw chat) emits a fact derived from model output. | Treat as plausibly-true; verify before acting. |
| `tool` | A tool call returns structured data. | High trust if the tool itself is trusted; carries the tool's own confidence if available. |
| `user` | A human input arrives via API or UI. | Authoritative for the user's domain — typically pinned at confidence 1.0. |
| `rule` | A Bosun/CLIPS rule asserts a derived fact in its RHS. | Symbolic derivation; confidence inherited from premises (min by default). |
| `model` | A non-LLM ML model (classifier, regressor, embedder) emits a prediction. | Carry the model's calibrated probability as confidence. |
| `external` | A trigger or webhook injects facts at run start. | Trust depends on the trigger source. |

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

Halt if a user-origin fact contradicts a rule-origin fact:

```clips
(defrule user-overrides-rule
  (claim (subject ?s) (value ?v1) (origin user))
  (claim (subject ?s) (value ?v2&~?v1) (origin rule))
  =>
  (assert (control halt))
  (assert (audit (reason "user contradicts rule") (subject ?s))))
```

Prefer model-origin facts over llm-origin for the same key:

```clips
(defrule prefer-model-over-llm
  ?bad <- (label (key ?k) (origin llm))
  (label (key ?k) (origin model))
  =>
  (retract ?bad))
```

## Confidence Convention

`confidence` is a float in `[0, 1]`. Each origin documents its calibration:

- `user` — typically 1.0 unless the UI captured uncertainty.
- `tool` — the tool's own confidence if it returns one; else 1.0 for deterministic tools, 0.9 default for retrieval scores normalized to [0, 1].
- `llm` — DSPy modules emit logprob-derived confidence when available; otherwise the convention is 0.7 default unless the prompt asks the model for a self-reported score.
- `model` — the calibrated probability (must be calibrated, not raw softmax, for downstream rules to mean what they say).
- `rule` — `min` of premise confidences by default; rules may override with explicit aggregation.
- `external` — set by the trigger; webhooks default to 1.0, file watchers to 1.0, MCP-injected facts inherit from the source.

Sources should document their calibration in their skill or pack README.

## Querying History

Facts are indexed by `run_id` and `step`. Access:

CLI:

```bash
harbor facts list --run <run_id>
harbor facts list --run <run_id> --origin tool --since-step 12
harbor facts get --run <run_id> --step 7
```

Python:

```python
from harbor.client import HarborClient

c = HarborClient()
facts = c.facts.list(run_id="r-abc123", origin="tool", min_confidence=0.8)
for f in facts:
    print(f.step, f.source, f.body)
```

REST:

```
GET /v1/runs/{run_id}/facts?origin=tool&min_confidence=0.8&since_step=12
```

The fact log is append-only and persisted by the configured FactStore provider. Replays consume this log to reconstruct any prior CLIPS state.
