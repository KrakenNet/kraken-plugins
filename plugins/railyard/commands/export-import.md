---
description: Export and import entity configurations for portability across Railyard environments
argument-hint: [export|import] [--type agent|tool|governor|workflow] [--scope entity|dependencies|environment]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Export/Import

Export entity configurations as portable bundles and import them into other environments.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `export` (default), `import`
- **--type**: Pre-select entity type
- **--scope**: Pre-select export scope

## Route by Action

### Export (default)

Interview:

1. **"What type of entity to export?"**
   - agent
   - tool
   - governor
   - workflow

2. List entities of that type and ask **"Which one?"** (entity_id)

3. **"Export scope?"**
   - entity — Just this entity's configuration
   - dependencies — Entity + all tools, governors, credentials it references
   - environment — Full environment snapshot including all linked entities

Execute:
```bash
BUNDLE=$(curl -s -X POST "${RAILYARD_URL}/api/v1/export" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"entity_type":"...","entity_id":"uuid","scope":"dependencies"}')
```

4. **"Save bundle to file?"** (optional — write JSON to local file)

If yes, save the bundle JSON to the specified path.

Show summary:
```
Exported: <entity_type> "<name>"
  Scope: <scope>
  Includes:
    Agents: N
    Tools: N
    Governors: N
    Workflows: N
    Credentials: N (placeholders — secrets not exported)
```

### Import

Interview:

1. **"Path to bundle file, or paste the JSON?"**

2. **"Dry run first?"** (yes recommended — validates without creating)

Dry run:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/import?dry_run=true" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "bundle=@bundle.json"
```

If validation passes and user confirms:
```bash
RESULT=$(curl -s -X POST "${RAILYARD_URL}/api/v1/import" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "bundle=@bundle.json")
```

Show summary:
```
Imported:
  Agents: N created
  Tools: N created
  Governors: N created
  Workflows: N created
  Credentials: N placeholders (configure secrets manually)

⚠ Credential placeholders need secrets:
  - credential-name-1
  - credential-name-2
```

## Report

Show the output to the user.
