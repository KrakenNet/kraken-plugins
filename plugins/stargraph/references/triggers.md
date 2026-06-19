# Stargraph Triggers

Reference for triggers: how runs get initiated by external events.

Triggers are pluggy plugins that emit `TriggerEvent` objects into the scheduler
queue. They are authored in `triggers.yaml` under the runtime config dir
(`~/.config/stargraph/triggers.yaml`, overridable via `STARGRAPH_CONFIG_DIR`) and
loaded at `stargraph serve` startup.

## Built-in trigger types

There are exactly three built-ins:

| Type | Use when | Module |
|---|---|---|
| `manual` | Default. Runs kicked off via `stargraph run` or `POST /v1/runs`. | `stargraph.triggers.manual` |
| `cron` | Scheduled, recurring runs (digests, sweeps, polls). | `stargraph.triggers.cron` |
| `webhook` | External system push (GitHub, Linear, Slack, …). | `stargraph.triggers.webhook` |

(`mcp_adapters` is a plugin group, not a trigger kind. There is no `file_watch`
built-in.)

## triggers.yaml schema

A top-level `version: "1.0"` followed by per-kind lists:

```yaml
version: "1.0"

manual:
  - id: research-adhoc
    graph_id: research
    description: "Ad-hoc research run"

cron:
  - id: cron:nightly-research
    graph_id: research
    expr: "0 3 * * *"          # standard 5-field cron
    tz: UTC                     # IANA name; resolved at init
    missed_fire_policy: fire_once_catchup   # or: skip
    params:
      query: "weekly digest"

webhook:
  - id: webhook:github-pr
    graph_id: pr_triage
    path: /triggers/github               # must start with /; mounted by the webhook trigger
    timestamp_window_seconds: 300
    nonce_lru_size: 10000
    current_secret_env: STARGRAPH_WEBHOOK_SECRET_CURRENT
    previous_secret_env: STARGRAPH_WEBHOOK_SECRET_PREVIOUS
```

## Cron triggers

The cron trigger uses `cronsim.CronSim` for DST-safe expressions (5-field cron
only). On `start` it spawns one background `asyncio.Task` per spec that computes
`next_fire`, sleeps until then, derives the idempotency key, and enqueues.

- `tz` is an IANA timezone name (e.g. `UTC`, `America/New_York`), resolved at
  init — bad config fails fast.
- `missed_fire_policy`: `fire_once_catchup` (default) fires once for the most
  recent missed scheduled time so the idempotency key matches a never-down
  system; `skip` jumps straight to the next future fire.
- **Idempotency key**: `sha256(trigger_id || scheduled_fire.isoformat())`. The
  ISO format includes the tz offset, so the same wall-clock instant in different
  zones produces distinct keys.

## Webhook triggers

The webhook trigger mounts a FastAPI `POST` route per spec and verifies inbound
bodies with a Stripe-style HMAC-SHA256 signature before enqueueing a run.

- The route is mounted at `path` on the running `stargraph serve` app.
- `current_secret_env` / `previous_secret_env` name the environment variables
  holding the HMAC keys (e.g. `STARGRAPH_WEBHOOK_SECRET_CURRENT` /
  `STARGRAPH_WEBHOOK_SECRET_PREVIOUS`). `current_secret` is used for both signing
  and verification; `previous_secret` is valid for verification only (rotation
  grace).
- Verification gauntlet (in order): read `X-Stargraph-Timestamp` /
  `X-Stargraph-Signature` headers → timestamp within `timestamp_window_seconds`
  → constant-time HMAC compare against current then previous → nonce LRU replay
  check → enqueue.
- **Idempotency key**: `sha256(trigger_id || sha256(raw_body))`.
- Status codes: `401` on missing headers / out-of-window timestamp / bad HMAC;
  `409` on a duplicate nonce; `400` on malformed JSON body.

## Manual triggers

The `manual` trigger is the convergence point for operator-initiated runs: both
`stargraph run` and `POST /v1/runs` resolve to the same `enqueue` call. List an
entry in `triggers.yaml` to document an intended manual entry point; it has no
on-disk polling behavior.

```bash
curl -fsS -X POST "http://localhost:8000/v1/runs" \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"research","params":{"query":"…"}}'
```

Retrieve the run handle via `GET /v1/runs/{run_id}`.

## TriggerEvent

Every trigger emits a `stargraph.triggers.TriggerEvent` into the scheduler queue:

| Field | Type | Description |
|---|---|---|
| `trigger_id` | `str` | Emitting trigger instance (e.g. `"cron:nightly-research"`). |
| `scheduled_fire` | `datetime` | Canonical fire time (cron-tick instant; receipt time for webhook/manual). |
| `idempotency_key` | `str` | Pre-computed dedup key; the scheduler dedupes against pending-run state before enqueueing. |
| `payload` | `dict` | JSON-serializable parameters forwarded to the run as `params`. |

`TriggerEvent` carries `extra='forbid'`, so `payload` is the escape hatch for
trigger-specific data.

## Trigger plugins

To add a new trigger family, build a plugin that registers under the
`stargraph.triggers` entry-point group (name → `TriggerPlugin` class):

```toml
[project.entry-points."stargraph.triggers"]
my_trigger = "my_pkg.triggers:MyTriggerPlugin"
```

A trigger implements the `Trigger` protocol — `init(deps)` / `start()` /
`stop()` / `routes()`. The serve lifespan dispatches these per-plugin with
exception isolation so one bad trigger cannot block the others.

## Verifying a trigger

Add the entry to `triggers.yaml`, start `stargraph serve`, and confirm the
scheduler picks it up:

- Cron: a background task is spawned per spec.
- Webhook: its `POST` route is mounted — confirm the mounted path and that the
  target graph appears in `GET /v1/graphs`.

## Authoring checklist

- [ ] Cron triggers declare `tz` explicitly (don't trust the host); a UTC server
      is recommended for air-gapped deployments.
- [ ] Webhook secrets live in env vars named by `current_secret_env` /
      `previous_secret_env`, never in YAML.
- [ ] `params` / webhook body is shaped to the target graph's state schema —
      validate by loading the graph with `stargraph run GRAPH --inspect`.
- [ ] Webhook `path` starts with `/` and is unique across triggers.
