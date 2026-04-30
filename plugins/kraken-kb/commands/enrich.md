---
description: Add external reference material (library docs, protocol specs, API guides) to KB articles
argument-hint: <path|domain> [--dry-run]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch]
---

# KB Enrich

Add external reference material to KB articles by identifying dependencies in source code and fetching relevant documentation.

## Parse Arguments

From `$ARGUMENTS`:
- **Required**: `<path>` (e.g., `governors/runtime.md`) or `<domain>` (e.g., `governors`)
- **--dry-run**: show what would be added without modifying files

## Resolve Targets

### Single Article
1. Verify exists: `test -f docs/<path>`
2. If missing: error "Article not found at docs/<path>"

### Domain
1. Find all articles: `find docs/<domain>/ -name "*.md" -not -name "*-gaps.md" | sort`
2. Process each article

## For Each Article

### 1. Read the Article
Read `docs/<path>` to understand what domain/scope it covers.

### 2. Read Associated Source Files
Look up the domain's source files from the domain map in kb-conventions skill. Read the key source files to identify external dependencies.

### 3. Identify External Dependencies

Scan source files for:
- **Go imports**: extract `import` blocks, filter to non-stdlib, non-internal packages
  ```bash
  grep -h "\"" <go-files> | grep -v "internal/" | grep -v "\"fmt\"" | sort -u
  ```
- **Library references**: look for comments mentioning external tools, protocols, or libraries
- **Known frameworks**: go-chi, DSPy-Go, CLIPS, React, Tailwind, Shadcn, pgvector, Supabase

### 4. Fetch Documentation

For each identified external dependency:
1. Search for official documentation using WebSearch
2. Fetch key pages using WebFetch
3. Extract: API patterns, key functions, gotchas, version-specific behavior
4. Focus on facts relevant to HOW this project uses the dependency

### 5. Add External References Section

If `--dry-run`: report what would be added and stop.

Otherwise, add or update `## External References` section at the end of the article (before `## Do Not` if present):

```markdown
## External References

### <Library/Protocol Name>
- **Docs**: <URL>
- **Key facts**: <1-3 bullet points relevant to this domain>
- **Version**: <version constraint if applicable>
```

### 6. Check Line Limits

After adding references:
- If article exceeds 200 lines: move the External References section to a companion file `docs/<domain>/<name>-refs.md` and replace with a link: `See [external references](<name>-refs.md)`
- The refs file uses the same frontmatter format with scope suffixed `-refs`

## Report

For each article processed:
```
## Enriched: <path>
- Added N external references: <list>
- Line count: N (within limits | moved to refs file)
```
