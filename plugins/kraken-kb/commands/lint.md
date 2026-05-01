---
description: Run health checks on KB internal consistency — frontmatter, links, line counts, routing
argument-hint: [domain]
allowed-tools: [Bash, Read, Glob, Grep, Agent]
---

# KB Lint

Check the Knowledge Base for formatting errors, broken links, missing sections, and routing inconsistencies.

## Parse Arguments

From `$ARGUMENTS`:
- **Optional**: domain name to limit lint scope (e.g., `agents`, `governors`)

## Delegate

Delegate to `kb-linter` agent via Agent tool with:
- domain_filter: the domain name if provided, otherwise omit

## Report

Show the agent's report to the user, grouped by severity:
1. **ERRORS** — must fix (missing frontmatter, broken links, over 300 lines)
2. **WARNINGS** — should fix (over 200 lines, unlinked domain references)
3. **INFO** — optional (orphan articles not in _index.md)

Include the summary line with counts.
