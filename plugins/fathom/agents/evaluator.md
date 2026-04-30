---
description: Driver for Fathom evaluation flows — POST /v1/evaluate; render decision + reason + attestation; surface audit id.
tools: [Bash, Read, Write]
---

# Evaluator

## Inputs

- `facts` (list of dict)
- `ruleset` (optional)
- `FATHOM_URL`, `FATHOM_TOKEN`

## Steps

1. Build body: `{"facts": [...], "ruleset": "...", "request_id": "<uuid>"}`.
2. POST to `${FATHOM_URL}/v1/evaluate`.
3. Parse envelope; extract `decision`, `reason`, `duration_us`, `attestation`, `audit_id`.
4. Verify attestation header alg=EdDSA; truncate token to first 64 chars for display.

## Output

Markdown block with decision + reason + duration + attestation snippet + audit_id.
