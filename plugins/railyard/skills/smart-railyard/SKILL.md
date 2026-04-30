---
name: smart-railyard
description: This skill should be used when any railyard command or agent needs auth flow, base URL configuration, API conventions, response envelope parsing, credential access helpers, or the verify-before-call pattern. Core behavioral skill for all Railyard Operations plugin commands.
version: 1.0.0
user-invocable: false
---

# Smart Railyard

Core skill for all Railyard plugin commands and agents. Defines auth flow, API conventions, and shared patterns.

## API Configuration

| Setting | Default | Override |
|---------|---------|----------|
| Base URL | `http://localhost:38080` | `RAILYARD_URL` env var |
| Anon Key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzczNjE2NjAyLCJleHAiOjIwODg5NzY2MDJ9.R8fmvo9voi7gKhqc5SkQD20WYTuIvQ4FMavKj4XNNZI` | `SUPABASE_ANON_KEY` env var |
| Auth token | None (must authenticate) | `RAILYARD_TOKEN` env var |

## Auth Flow

Every command must have a valid JWT before making API calls.

### Token Resolution Order

1. Check `RAILYARD_TOKEN` env var — use if set
2. Check if token was cached earlier in session
3. If neither: prompt user to run `/railyard:auth` first

### Obtaining a Token

```bash
# Login to Supabase GoTrue
RAILYARD_URL="${RAILYARD_URL:-http://localhost:38080}"
ANON_KEY="${SUPABASE_ANON_KEY:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzczNjE2NjAyLCJleHAiOjIwODg5NzY2MDJ9.R8fmvo9voi7gKhqc5SkQD20WYTuIvQ4FMavKj4XNNZI}"

TOKEN=$(curl -s "${RAILYARD_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
  | jq -r '.access_token')
```

### Default Dev Credentials

For local development:
- Email: `dev@railyard.local`
- Password: `AB&P$7Np3teJrPu9PZaD`

## API Conventions

### Making Authenticated Calls

All API calls use this pattern:

```bash
curl -s "${RAILYARD_URL}/api/v1/<endpoint>" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

### Response Envelope

Success:
```json
{"success": true, "data": {...}, "meta": {"total": N, "limit": 20, "offset": 0, "count": N}}
```

Error:
```json
{"success": false, "error": {"code": "not_found", "message": "...", "details": ""}}
```

### Parsing Responses

Always extract data from envelope:
```bash
RESULT=$(curl -s ... | jq '.')
SUCCESS=$(echo "$RESULT" | jq -r '.success')
if [ "$SUCCESS" != "true" ]; then
  ERROR=$(echo "$RESULT" | jq -r '.error.message')
  echo "API Error: $ERROR"
fi
DATA=$(echo "$RESULT" | jq '.data')
```

### Pagination

All list endpoints: `?limit=N&offset=M` (defaults: limit=20, offset=0, max=100)

## Cursor Pagination

Some list endpoints support cursor pagination for stable iteration over large result sets:
- `/api/v1/executions/{id}/steps` — clamped at limit=200
- `/api/v1/executions/{id}/trace` — clamped at limit=200

Pattern:

```bash
URL="${RAILYARD_URL}/api/v1/executions/$EXEC_ID/steps?limit=200"
while [ -n "$URL" ]; do
  RESP=$(curl -s "$URL" -H "Authorization: Bearer ${TOKEN}")
  echo "$RESP" | jq '.data[]'
  NEXT=$(echo "$RESP" | jq -r '.meta.next_cursor // empty')
  [ -z "$NEXT" ] && break
  URL="${RAILYARD_URL}/api/v1/executions/$EXEC_ID/steps?limit=200&cursor=$NEXT"
done
```

If a list endpoint returns >200 rows without a cursor, fall back to `?offset=&limit=`.

## WS Streaming Helpers

Long-running flows can attach to WebSocket endpoints for real-time updates. Each frame is JSON with at least:

```json
{"seq": 42, "event_type": "step.completed", "payload": {...}, "timestamp": "2026-04-30T12:00:00Z"}
```

Connect via `websocat` (or any WS client) using the same bearer token. The base URL is the HTTP base with the scheme swapped to `ws`/`wss`.

### Execution Livetail — `/api/v1/ws/v1/executions/<execId>/events?since=<seq>`

Replays from the ExecutionHub buffer (last 1000 events) when `since` is set, then streams live.

```bash
websocat -H "Authorization: Bearer $TOKEN" \
  "${RAILYARD_URL/http/ws}/api/v1/ws/v1/executions/$EXEC_ID/events?since=0"
```

### Training Progress — `/api/v1/ws/training/<runId>`

```bash
websocat -H "Authorization: Bearer $TOKEN" \
  "${RAILYARD_URL/http/ws}/api/v1/ws/training/$RUN_ID"
```

### User Notifications — `/api/v1/ws/notifications`

User-scoped fan-out of notification events.

```bash
websocat -H "Authorization: Bearer $TOKEN" \
  "${RAILYARD_URL/http/ws}/api/v1/ws/notifications"
```

### Trace Monitor — `/api/v1/ws/traces/monitor`

Live span/trace events across the platform.

```bash
websocat -H "Authorization: Bearer $TOKEN" \
  "${RAILYARD_URL/http/ws}/api/v1/ws/traces/monitor"
```

### Chat — `/api/v1/ws/chat/<sessionId>`

```bash
websocat -H "Authorization: Bearer $TOKEN" \
  "${RAILYARD_URL/http/ws}/api/v1/ws/chat/$SESSION_ID"
```

## Verify-Before-Call Pattern

1. **Health check first**: `GET /api/v1/health` — confirm API is reachable
2. **List before create**: Check existing entities to avoid duplicates
3. **GET after create**: Confirm entity was created, capture computed fields (id, created_at)
4. **Parse errors**: On failure, extract error message from envelope — don't retry blindly

## Credential Access Helper

Cross-cutting pattern for commands that need credentials:

1. List: `GET /api/v1/credentials?limit=100`
2. Present matches as numbered choices
3. If none match: offer to create inline (delegate to credential-manager agent)
4. Return selected `credential_id`

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 401 | Token expired/invalid | Prompt re-auth via `/railyard:auth` |
| 409 | Duplicate entity | Offer to use existing or rename |
| 422 | Validation error | Parse details, explain, ask correction |
| 429 | Rate limit (per-user limiter from `feat(unlimited-void)`) | Back off using `Retry-After` header; surface to user if persistent |
| 500/503 | Server error | "API down — is the container running?" |

### Workflow Execution Notes

`POST /api/v1/workflows/{id}/execute` accepts an optional `execution_name` field — a human-readable nickname surfaced in execution lists, traces, and the livetail WS. Pass it through whenever the user supplies one (e.g. via `--nickname` on `/railyard:workflow`).

## Build-Test-Fix Loop

Agents creating testable entities run this loop (max 5 iterations):

1. Create/update entity via API
2. Test entity (start, execute, test endpoint)
3. If pass: done
4. If fail: parse error, diagnose via traces/status/runtime
5. Fix via PUT update
6. Back to step 2
7. After 5 failures: stop, full diagnostic dump

## Communication Style

- Extreme brevity. Fragments over sentences.
- Tables over prose. Bullets over paragraphs.
- End with action steps.
- Surface questions early.
