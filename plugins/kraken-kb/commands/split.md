---
description: Analyze and decompose oversized or overloaded KB articles into focused sub-articles
argument-hint: <path|domain> [--dry-run] [--auto]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, Agent]
---

# KB Split

Analyze KB articles for split signals and decompose them into focused sub-articles.

## Parse Arguments

From `$ARGUMENTS`:
- **Required**: `<path>` (e.g., `agents/overview.md`) or `<domain>` (e.g., `agents`)
- **--dry-run**: show recommended splits without executing
- **--auto**: execute splits without asking for confirmation

## Resolve Targets

### Single Article
1. Verify exists: `test -f docs/<path>`
2. Analyze that article

### Domain
1. Find all articles: `find docs/<domain>/ -name "*.md" -not -name "*-gaps.md" -not -name "*-refs.md" | sort`
2. Analyze each article

## Analyze Each Article

Read the article and check for split signals:

### 1. Line Count
```bash
wc -l docs/<path>
```
- Over 200 lines: SPLIT SIGNAL (soft max exceeded)
- Over 300 lines: MUST SPLIT (hard max violated)

### 2. Concept Count
Count `## ` level-2 headings in the article body (excluding frontmatter).
- More than 6 distinct sections: SPLIT SIGNAL (article covers too many concepts)

### 3. Source File Fan-Out
Read the article and count unique source files referenced (paths in code blocks, Conventions section, etc.).
- More than 5 unrelated source files: SPLIT SIGNAL

### 4. Mixed Scope
Check if the article covers BOTH:
- Configuration/CRUD behavior (schema, API endpoints, create/update flows)
- Runtime/execution behavior (how it runs, lifecycle, internal algorithms)

If both are present and substantial: SPLIT SIGNAL (should be separate overview.md and execution.md)

## Propose Split Plan

For each article with split signals, generate a plan:

```
## Split: <article-path>
Signals: <which signals triggered>

### Proposed new articles:
1. <domain>/<new-scope-1>.md — <what sections move here>
2. <domain>/<new-scope-2>.md — <what sections move here>

### Original article keeps:
- <which sections remain>

### Cross-link updates:
- <article> gains link to <new-article>
- <other-articles> that referenced sections in original need link updates
```

## Execute

If `--dry-run`: report the plan and stop.

If `--auto` or user confirms each split:

1. For each new article: delegate to `kb-writer` agent with action=create, providing the sections being moved as user_notes context
2. Edit the original article: remove moved sections, add links to new articles in their place
3. Update `docs/_index.md`: add routing entries for new articles
4. Find all articles that link to the original and update any broken section anchors
5. If a gap file exists for the original, check if any gaps should move to the new articles

## Report

```
## Split Results

### <original-path>
- Kept: N lines, M sections
- Created: <new-path-1> (N lines), <new-path-2> (N lines)
- Updated _index.md: added N routing entries
- Updated N cross-links in other articles
```
