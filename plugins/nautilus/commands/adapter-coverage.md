---
description: Generate a SN-style coverage matrix for a Nautilus adapter (P2 issue)
argument-hint: <adapter-name>
allowed-tools: [Bash, Read, Write]
---

# Adapter Coverage Matrix

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Run

Read the adapter's source file(s). Extract every endpoint or data_type the adapter handles, classify each as ✅ first-class / ⚠️ generic-rest with sample URL / ❌ not covered. Render as a markdown table at `docs/reference/adapters/<adapter>.md`.

## Report

Table + the diff applied to docs.
