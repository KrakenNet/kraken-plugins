---
description: Obtain or manage Supabase JWT tokens for Railyard API access
argument-hint: [--dev]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Auth

Obtain a JWT token for authenticating with the Railyard API.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API configuration and auth flow.

## Check Existing Token

First, check if a token is already available:

```bash
RAILYARD_URL="${RAILYARD_URL:-http://localhost:38080}"

# Check if API is reachable
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${RAILYARD_URL}/api/v1/health")
if [ "$HEALTH" != "200" ]; then
  echo "ERROR: Railyard API not reachable at ${RAILYARD_URL}"
  echo "Is the Docker container running? Try: docker compose up -d"
  exit 1
fi
```

If `RAILYARD_TOKEN` env var is set, verify it works:

```bash
if [ -n "$RAILYARD_TOKEN" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${RAILYARD_URL}/api/v1/agents?limit=1" \
    -H "Authorization: Bearer ${RAILYARD_TOKEN}")
  if [ "$STATUS" = "200" ]; then
    echo "Existing token is valid."
    exit 0
  fi
fi
```

## Parse Arguments

From `$ARGUMENTS`:
- **--dev**: Use default dev credentials (`dev@railyard.local`) without prompting

## Interview (if not --dev)

If `--dev` flag is NOT present, ask the user:

1. "Do you have an existing account or need to create one?" (existing / new)
2. "What is your email?"
3. "What is your password?"

## Authenticate

### For --dev or known credentials:

```bash
RAILYARD_URL="${RAILYARD_URL:-http://localhost:38080}"
ANON_KEY="${SUPABASE_ANON_KEY:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzczNjE2NjAyLCJleHAiOjIwODg5NzY2MDJ9.R8fmvo9voi7gKhqc5SkQD20WYTuIvQ4FMavKj4XNNZI}"

RESULT=$(curl -s "${RAILYARD_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$RESULT" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ]; then
  ERROR=$(echo "$RESULT" | jq -r '.error_description // .msg // "Unknown error"')
  echo "Auth failed: $ERROR"
else
  echo "Authenticated successfully."
  echo "Token (set as RAILYARD_TOKEN): ${TOKEN}"
fi
```

### For new account (signup):

```bash
RESULT=$(curl -s "${RAILYARD_URL}/auth/v1/signup" \
  -H "apikey: ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$RESULT" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ]; then
  ERROR=$(echo "$RESULT" | jq -r '.error_description // .msg // "Unknown error"')
  echo "Signup failed: $ERROR"
else
  echo "Account created and authenticated."
  echo "Token: ${TOKEN}"
fi
```

## Output

Report the token and how to use it:

```
Authenticated as: <email>
Token: <jwt>

Use in this session — all railyard commands will use this token.
Or set: export RAILYARD_TOKEN=<jwt>
```
