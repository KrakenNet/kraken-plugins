# Harbor Triggers

Reference for trigger plugins: how runs get initiated by external events.

## Built-in trigger types

| Type | Use when | Plugin entry-point |
|---|---|---|
| `manual` | Default. Runs kicked off via `POST /v1/runs` (or `harbor run`). | `harbor.triggers.manual:ManualTrigger` |
| `cron` | Scheduled, recurring runs (digests, sweeps, polls). | `harbor.triggers.cron:CronTrigger` |
| `webhook` | External system push (GitHub, Linear, Slack, …). | `harbor.triggers.webhook:WebhookTrigger` |

Other trigger types (`mcp`, `file_watch`) are reserved for future plugins —
ship them as separate distributions when needed.

## Cron triggers

Harbor's scheduler uses `cronsim` for DST-safe expressions. 5-field cron only.

```yaml
triggers:
  - name: nightly_research
    type: cron
    cron: "0 3 * * *"          # 03:00 every day
    timezone: UTC               # default; or America/Los_Angeles
    dedup_key: research:nightly
    jitter_seconds: 60          # optional; spreads cluster-wide load
    input:
      query: "weekly digest"
```

**Per-graph capacity** is enforced by `anyio.CapacityLimiter` honoring the
graph IR's `concurrency`. Two firings in the same minute won't trample each
other; the second waits or is dropped depending on `concurrency` policy.

**Idempotency**: `dedup_key` is BLAKE3-keyed by the scheduler. Re-firings
with the same key inside a graph's `dedup_window` are coalesced.

## Webhook triggers

```yaml
triggers:
  - name: github_pr
    type: webhook
    path: /hooks/github-pr
    secret_env: HARBOR_HOOK_GITHUB_PR    # HMAC verify on inbound POST
    method: POST                          # default
    dedup_key: gh:${headers.x-github-delivery}
    input_template:                       # JSON-pointer mapping
      pr_number: /pull_request/number
      repo:      /repository/full_name
      action:    /action
```

- `${HARBOR_URL}/hooks/github-pr` returns `202 {run_id}` on accept,
  `401` on bad HMAC, `409` on dedup hit.
- `secret_env` MUST be set in the deployment env. Cleared profile refuses
  to register a webhook trigger missing the secret.
- `input_template` resolves JSON pointers against the request body and a
  small `${headers.*}` namespace. Missing pointers are nullable; type
  coercion follows the graph's State schema.

## Manual triggers

No YAML entry. The `manual` plugin is always registered. `POST /v1/runs`
with `{graph, input}` is the canonical entry point.

```bash
curl -fsS -X POST "${HARBOR_URL}/v1/runs" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"graph":"research","input":{"query":"…"}}'
```

## Listing & introspection

```bash
GET  /v1/triggers                  # all triggers, all graphs
GET  /v1/triggers?graph=research   # per graph
GET  /v1/triggers/<name>           # next_fire_at, last_fire_at, fire_count
```

`harbor.yaml` is the source of truth; the scheduler reconciles on graph
register/update. There is no separate trigger CRUD API — change the YAML,
re-register the graph.

## Authoring checklist

- [ ] Every trigger has a `dedup_key` — never rely on accidental uniqueness.
- [ ] Webhook secrets live in env vars, not in YAML.
- [ ] Cron triggers declare `timezone` explicitly (don't trust the host).
- [ ] `input` / `input_template` is shaped to the graph's State schema —
      run `harbor graph verify` after editing.
- [ ] Cleared deployments: webhook triggers only with a registered HMAC secret.
