---
description: Find KB articles whose source code has changed since they were last updated
argument-hint: [domain]
allowed-tools: [Bash, Read, Glob, Grep, Agent]
---

# KB Stale

Detect KB articles that may be outdated because their source code has been modified more recently.

## Parse Arguments

From `$ARGUMENTS`:
- **Optional**: domain name to limit scope (e.g., `agents`, `governors`)

## Delegate

Delegate to `kb-auditor` agent via Agent tool with:
- action: stale
- domain_filter: the domain name if provided, otherwise omit

## Report

Show the agent's staleness report:
- Table of stale articles sorted by days behind (most stale first)
- For each: article path, last updated date, which source file changed, when, days behind
- Summary: total articles checked, how many stale, how many fresh
