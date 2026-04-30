---
description: Refresh a KB article to match current source code
argument-hint: <path> | <domain>
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, Agent]
---

# KB Update Article

Refresh one or more KB articles by comparing them against current source code.

## Parse Arguments

From `$ARGUMENTS`:
- **Single article**: a path like `agents/overview.md` — update that one article
- **Domain name**: a bare domain like `agents` or `governors` — update all articles in that domain

## Resolve Targets

### Single Article

1. Verify the article exists:
   ```bash
   test -f docs/<path> && echo "EXISTS" || echo "MISSING"
   ```
2. If MISSING: error "Article not found at docs/<path>. Use /kb:new to create it."
3. Read the article's frontmatter to get the domain
4. Look up source files from the domain map in kb-conventions

### Domain

1. Find all articles in the domain:
   ```bash
   find docs/<domain>/ -name "*.md" -not -name "*-gaps.md" | sort
   ```
2. For each article, delegate separately (or batch if few enough)

## Delegate

For each article to update, delegate to `kb-writer` agent via Agent tool with:
- action: update
- article_path: relative path from docs/
- domain: the domain
- source_files: list of source file paths from the domain map

If updating a whole domain with multiple articles, dispatch agents in parallel.

## Report

Show the agent's output summary for each updated article.
