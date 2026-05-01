---
description: Wire a trigger (manual / cron / webhook) onto a Harbor graph and verify scheduler pickup
argument-hint: <graph> --type manual|cron|webhook [--cron <expr>] [--path <url>] [--name <id>]
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion]
---

# New Trigger

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/triggers.md`.

## Parse Arguments

- `<graph>` (required) — graph the trigger fires on.
- `--type` ∈ {`manual`, `cron`, `webhook`}. Required.
- `--cron <expr>` — cronsim expression, required when type=cron. Use 5-field cron;
  Harbor scheduler is DST-safe.
- `--path <url-suffix>` — public path for webhook. Required when type=webhook.
- `--name <id>` — trigger ID. Auto-generated from `(graph, type, idx)` if omitted.

If a required arg is missing for the chosen type, prompt with AskUserQuestion.

## Edit harbor.yaml

Add a `triggers:` block on the graph:

```yaml
triggers:
  - name: nightly_research
    type: cron
    cron: "0 3 * * *"
    timezone: UTC
    dedup_key: research:nightly
    input:
      query: "weekly digest"
```

For webhooks, also generate an HMAC secret and store in `.env.example`:

```yaml
  - name: github_pr
    type: webhook
    path: /hooks/github-pr
    secret_env: HARBOR_HOOK_GITHUB_PR
    dedup_key: gh:${headers.x-github-delivery}
```

For manual triggers (the default), no scheduler entry — runs are kicked off via
`POST /v1/runs` or `/harbor:run`.

## Verify

```bash
uv run harbor graph verify "${GRAPH}"
curl -fsS "${HARBOR_URL}/v1/triggers" -H "Authorization: Bearer ${HARBOR_TOKEN}" | \
  jq --arg g "${GRAPH}" '.data[] | select(.graph == $g)'
```

For cron: ensure the scheduler picked it up — `next_fire_at` should be populated.
For webhook: hit it with a sample payload and confirm a 202 + `run_id`.

## Report

- Trigger ID, graph, type, schedule/path
- Dedup key
- For webhook: signed-cURL example for testing
- For cron: next 3 fire times (use cronsim if available locally)
