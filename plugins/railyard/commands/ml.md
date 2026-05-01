---
description: Manage Railyard ML stack — model definitions, trained models, training runs, datasets, layer schemas, ONNX import, image staging
argument-hint: [definitions|trained|runs|datasets|layers|onnx|images] [create|list|get|delete] [id?]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard ML Stack

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Ensure valid JWT. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Resource** (required): `definitions`, `trained`, `runs`, `datasets`, `layers`, `onnx`, `images`.
- **Action** (default `list`): `create`, `list`, `get`, `delete`.
- **ID** (optional, required for `get`/`delete`).

## Endpoint Map

| Resource | Endpoint root |
|---|---|
| definitions | /api/v1/model-definitions |
| trained | /api/v1/trained-models |
| runs | /api/v1/training-runs |
| datasets | /api/v1/ml-datasets |
| layers | /api/v1/ml/layer-schemas |
| onnx | /api/v1/onnx |
| images | /api/v1/images |

## Route by Action

### list

```bash
curl -s "${RAILYARD_URL}<endpoint>?limit=50" -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, status}'
```

### get

```bash
curl -s "${RAILYARD_URL}<endpoint>/<id>" -H "Authorization: Bearer ${TOKEN}" | jq '.data'
```

### create

Delegate to `ml-builder` agent with the chosen resource and an interview tailored to the resource's schema.

### delete

Confirm with AskUserQuestion before:

```bash
curl -s -X DELETE "${RAILYARD_URL}<endpoint>/<id>" -H "Authorization: Bearer ${TOKEN}"
```

## Report

Render the resulting JSON as a table.
