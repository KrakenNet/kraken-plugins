---
description: Author a trigger in triggers.yaml (manual / cron / webhook) and verify scheduler pickup at serve startup
argument-hint: <graph-id> --type manual|cron|webhook [--cron <expr>] [--path <url>] [--id <id>]
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion]
---

# New Trigger

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/triggers.md`.

## Parse Arguments

- `<graph-id>` (required) — the `graph_id` the trigger enqueues.
- `--type` ∈ {`manual`, `cron`, `webhook`}. These are the ONLY three built-ins.
- `--cron <expr>` — 5-field cron expression, required when type=cron. Parsed by
  `cronsim` (DST-safe); invalid syntax fails at serve startup.
- `--path <url-suffix>` — HTTP path the webhook route mounts (must start with
  `/`). Required when type=webhook.
- `--id <id>` — trigger id (e.g. `cron:nightly-cve-feed`). Goes into the
  idempotency key, so it must be unique across the deployment.

If a required arg is missing for the chosen type, prompt with AskUserQuestion.

## Edit triggers.yaml

Triggers are authored in `~/.config/stargraph/triggers.yaml` (override the dir
with env `STARGRAPH_CONFIG_DIR`), loaded at `stargraph serve` startup. Top-level
`version: "1.0"`, then per-kind lists.

**manual** — no on-disk behavior; equals `stargraph run` + `POST /v1/runs`:

```yaml
version: "1.0"
manual:
  - id: digest-now
    graph_id: <graph-id>
    description: "Kick a digest run on demand."
```

**cron** — `cronsim`-driven background loop, one task per spec:

```yaml
cron:
  - id: cron:nightly-research
    graph_id: <graph-id>
    expr: "0 3 * * *"
    tz: UTC
    missed_fire_policy: fire_once_catchup
    params:
      query: "weekly digest"
```

**webhook** — HMAC-SHA256-verified POST route. Secrets live in env vars named
per-spec (set `STARGRAPH_WEBHOOK_SECRET_CURRENT` / `STARGRAPH_WEBHOOK_SECRET_PREVIOUS`
or your own var names) — never in the file:

```yaml
webhook:
  - id: webhook:github-pr
    graph_id: <graph-id>
    path: /triggers/github-pr
    timestamp_window_seconds: 300
    nonce_lru_size: 10000
    current_secret_env: STARGRAPH_WEBHOOK_SECRET_CURRENT
    previous_secret_env: STARGRAPH_WEBHOOK_SECRET_PREVIOUS
```

To build a *custom* trigger kind, ship a plugin under entry-point group
`stargraph.triggers` (name → `Trigger` class with `init/start/stop/routes`),
emitting `TriggerEvent{trigger_id, scheduled_fire, idempotency_key, payload}`
into the scheduler queue (deduped by `idempotency_key`).

## Verify

```bash
uv run stargraph serve --graph "<graph.yaml>"
```

On startup the scheduler picks the trigger up: cron spawns one `asyncio.Task`
per spec; webhook mounts its `POST` route. Confirm with `GET /v1/graphs` (graph
registered) and, for webhooks, that the mounted `path` answers. Default serve
URL is `http://localhost:8000`.

## Report

- Trigger id, graph_id, type, schedule/path.
- For webhook: the env vars holding the current/previous secrets and a signed
  sample (HMAC of `"{ts}.{body}"`, headers `X-Stargraph-Timestamp` /
  `X-Stargraph-Signature`).
- For cron: the 5-field expr and tz.
