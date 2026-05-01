---
description: Build Railyard ML resources (model definitions, trained models, training runs, datasets, ONNX imports) via REST API with build-test-fix verification.
tools: [Bash, Read, AskUserQuestion]
---

# ML Builder

Owns interviews + curl calls + verification for Railyard ML endpoints.

## Inputs

- `resource` — one of {definitions, trained, runs, datasets, layers, onnx, images}.
- `TOKEN`, `RAILYARD_URL`.

## Resource Schemas (interview prompts)

### definitions
- name, framework (pytorch|onnx|gomlx), input_schema (JSON Schema), output_schema, layers (list of layer specs).

### trained
- definition_id, training_run_id, artifact_url, metrics (accuracy/loss).

### runs
- definition_id, dataset_id, hyperparameters (lr, epochs, batch_size), gpu_required.

### datasets
- name, source_url, format (jsonl|parquet|csv), schema_id, split (train/val/test ratios).

### layers
- name, layer_type, params (units, activation, etc).

### onnx
- model_path or url, target_definition_id (optional).

### images
- file_path (multipart upload), purpose (training|inference).

## Steps

1. Resolve endpoint root from resource.
2. Run interview, build JSON body.
3. POST to endpoint with `Authorization: Bearer ${TOKEN}` and `Content-Type: application/json`.
4. Parse response envelope; extract `id`, `created_at`.
5. Verify by GET on the new id.

## Build-Test-Fix Loop

Max 5 iterations. On 422, parse `error.details`, re-prompt. On 409, offer rename or use existing.

## Output

The created entity as a single JSON block + a one-line summary table.
