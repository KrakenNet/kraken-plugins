---
description: Verify a detached Ed25519 .sig against a Fathom release artifact (wheel/tarball/rule-pack)
argument-hint: <artifact-path> [--pubkey <path>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Verify Artifact

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Parse Arguments

- `<artifact-path>` — path to `.whl`/`.tar.gz`/rule-pack archive.
- `--pubkey` — pubkey path; defaults to `~/.fathom/release-pubkey.pem`.

## Locate Signature

Looks for `<artifact-path>.sig` in same dir.

## Delegate

Task tool → `verifier` agent.

## Report

✓ valid signature with key fingerprint. Or ✗ with the reason.
