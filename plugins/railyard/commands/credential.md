---
description: Create, list, update, or test credentials for Railyard integrations
argument-hint: [create|list|delete] [--type api_key|oauth2|basic_auth|bearer_token|custom]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Credential Management

Manage credentials used by tools, governors, and integrations.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure a valid JWT token is available. If not, prompt user to run `/railyard:auth` first.

```bash
RAILYARD_URL="${RAILYARD_URL:-http://localhost:38080}"
# Verify token works
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${RAILYARD_URL}/api/v1/credentials?limit=1" \
  -H "Authorization: Bearer ${TOKEN}")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "000" ]; then
  echo "Not authenticated. Run /railyard:auth first."
  exit 1
fi
```

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`, `delete`
- **--type**: Filter or pre-select credential type

## Route by Action

### List

Delegate to `credential-manager` agent with `action: list`.

### Delete

Ask: "Which credential?" → list existing → user picks → delegate to `credential-manager` with `action: delete`.

### Create (default)

Interview:

1. **"What should this credential be called?"** (name)

2. **"What type of credential?"**
   - api_key — Single API key
   - oauth2 — OAuth2 client credentials + tokens
   - basic_auth — Username + password
   - bearer_token — Bearer token
   - custom — Custom JSON structure

3. **Per-type questions:**
   - api_key: "What is the API key?"
   - oauth2: "Client ID?", "Client Secret?", "Access Token?" (optional), "Refresh Token?" (optional)
   - basic_auth: "Username?", "Password?"
   - bearer_token: "What is the token?"
   - custom: "Paste the credential JSON"

4. **"Provider name?"** (optional — e.g., "openai", "anthropic", "servicenow")

5. **"Endpoint URL?"** (optional — e.g., "https://api.openai.com")

6. **"Test the credential after creation?"** (yes/no)

## Delegate

Delegate to `credential-manager` agent via Task tool with:
- action: create
- All interview answers
- TOKEN and RAILYARD_URL

## Report

Show the agent's output to the user.
