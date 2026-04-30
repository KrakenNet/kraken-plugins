---
description: Hot-reload Fathom rules via POST /v1/rules/reload (requires Fathom ≥0.4.0); confirm signed audit attestation
argument-hint: [--path <rules-dir>] [--inline-yaml <file>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Fathom Reload Rules

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Version Gate

```bash
VERSION=$(curl -s "${FATHOM_URL}/info" -H "Authorization: Bearer ${FATHOM_TOKEN}" | jq -r '.data.version')
```

If `$VERSION < 0.4.0`, abort with: "your fathom version $VERSION does not support hot-reload. Upgrade or restart with new rules."

## Capture Pre-Hash

```bash
HASH_BEFORE=$(curl -s "${FATHOM_URL}/info" -H "Authorization: Bearer ${FATHOM_TOKEN}" | jq -r '.data.ruleset_hash')
```

## Reload

```bash
curl -s -X POST "${FATHOM_URL}/v1/rules/reload" \
  -H "Authorization: Bearer ${FATHOM_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"path":"<rules-dir>"}' | jq '.'
```

## Verify Post-Hash

```bash
HASH_AFTER=$(curl -s "${FATHOM_URL}/info" -H "Authorization: Bearer ${FATHOM_TOKEN}" | jq -r '.data.ruleset_hash')
[ "$HASH_BEFORE" != "$HASH_AFTER" ] && echo "✓ ruleset changed: $HASH_BEFORE → $HASH_AFTER"
```

## Report

Hashes before/after + attestation snippet from response.
