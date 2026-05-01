---
description: Find codebase features not covered by the Knowledge Base
argument-hint: [domain]
allowed-tools: [Bash, Read, Glob, Grep, Agent]
---

# KB Audit

Find tables, enums, routes, modules, pages, and packages that exist in the codebase but have no KB coverage.

## Parse Arguments

From `$ARGUMENTS`:
- **Optional**: domain name to limit audit scope (e.g., `agents`, `governors`)

## Delegate

Delegate to `kb-auditor` agent via Agent tool with:
- action: audit
- domain_filter: the domain name if provided, otherwise omit

## Report

Show the agent's structured gap report to the user. For each gap category with findings, summarize:
- What's missing
- Suggested action (add to existing article vs. create new article)
