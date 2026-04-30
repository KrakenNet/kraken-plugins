---
description: Show Fathom engine version, current ruleset hash, and feature support matrix
argument-hint: []
allowed-tools: [Bash, Read]
---

# Fathom Info

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Run

If running engine reachable: `GET ${FATHOM_URL}/info`. Else: `uv run fathom info`.

## Report

Table: version, ruleset_hash, attestation_pubkey_fingerprint, hot_reload_supported, signed_artifacts_supported.
