---
description: Scaffold a new Nautilus adapter package (entry-point registration, Adapter SDK contract, tests)
argument-hint: <adapter-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Adapter

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/references/adapter-sdk.md`.

## Parse Arguments

`<adapter-name>` (kebab-case, e.g., "nautobot", "snowflake").

## Interview

1. **Backing API?** (REST, GraphQL, native client)
2. **Auth model?** (token, OAuth2, basic, none)
3. **Data types?** (devices, interfaces, etc.)
4. **Scope enforcement?** (native API permissions vs. broker-side filter)
5. **Test fixture?** (live URL or recorded fixture)

## Delegate

Task tool → `adapter-builder`.

## Report

Package tree, entry-point in pyproject.toml, conformance test status.
