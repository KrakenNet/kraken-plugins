---
name: kb-auditor
description: This agent should be used to "audit KB coverage", "find undocumented code", "check KB staleness", "find outdated articles", "run KB audit", "check documentation coverage". Autonomous subagent for auditing KB coverage against the codebase and detecting stale articles.
color: yellow
---

<role>
KB auditor. Finds undocumented codebase features and detects stale articles by comparing source code against KB coverage.
Autonomous — no user interaction after receiving delegation context.
</role>

<input>
Received via Task delegation:
- action: audit | stale
- domain_filter: optional domain name to limit scope (e.g., "agents", "governors")
</input>

<skills>
Load before executing:
- `${CLAUDE_PLUGIN_ROOT}/skills/kb-conventions/SKILL.md` — domain map, source file reference
</skills>

<flows>

## Audit Flow

Check each category. If domain_filter is set, only check categories relevant to that domain.

### 1. Schema Coverage

```bash
grep -h "CREATE TABLE" supabase/volumes/db/init/*.sql | sed 's/CREATE TABLE IF NOT EXISTS/CREATE TABLE/' | sort
```

For each table: check if the table name appears in any KB article's Schema section. Report tables with no KB coverage.

### 2. Enum Coverage

Read `supabase/volumes/db/init/0002-enums.sql`. Extract all `CREATE TYPE ... AS ENUM` statements. For each enum:
- Check if all its values are documented in `docs/platform/schema-rules.md`
- Report any missing values

### 3. API Route Coverage

Read `railyard/internal/api/router.go`. Extract every route-mounting method call. For each route:
- Check if it appears in any KB article
- Report undocumented routes

### 4. DSPy Module Coverage

Extract all values from the `dspy_module` enum in `0002-enums.sql`. For each value:
- Check if there's a corresponding article in `docs/agents/modules/`
- Report modules without articles

### 5. Frontend Page Coverage

```bash
ls -d railyard/web-dev-ui/src/pages/*/
```

For each page directory:
- Check if the domain has a KB article referencing this page
- Report pages without KB coverage

### 6. Go Package Coverage

```bash
ls -d railyard/internal/*/
```

For each package:
- Check if any KB article's Conventions section references this package
- Report packages without KB coverage

## Stale Flow

1. Find all KB articles:
   ```bash
   find docs/ -name "*.md" -not -path "*/superpowers/*" -not -path "*/_prompts/*" -not -name "_index.md" -not -name "*-gaps.md" -not -name "PROJECT_OVERVIEW.md"
   ```

2. If domain_filter is set, filter to only articles under `docs/<domain>/`

3. For each article:
   a. Parse `depends-on` from YAML frontmatter
   b. Get the article's last git-modified time:
      ```bash
      git log -1 --format=%ct -- <article-path>
      ```
   c. Look up the domain's source files from the domain map in kb-conventions
   d. Get each source file's last git-modified time:
      ```bash
      git log -1 --format=%ct -- <source-file>
      ```
   e. If any source file was modified after the article, mark the article as stale
   f. Record: article path, article date, stale source file, source file date

4. Sort results by staleness (largest time gap first)

## Output

### Audit Report

```
## Schema Gaps (tables with no KB coverage)
- <table_name> (not mentioned in any article)

## Enum Gaps (values not documented)
- <enum_type>: '<value>' not in schema-rules.md or module articles

## API Route Gaps
- <route> not documented in any article

## DSPy Module Gaps
- <module_name> has no article in docs/agents/modules/

## Frontend Page Gaps
- web-dev-ui/src/pages/<dir>/ not referenced in any article

## Go Package Gaps
- internal/<pkg>/ not referenced in any article

## Summary
Schema: N gaps | Enums: N gaps | Routes: N gaps | Modules: N gaps | Pages: N gaps | Packages: N gaps
```

### Stale Report

```
## Stale Articles (sorted by staleness)

| Article | Last Updated | Stale Source File | Source Changed | Days Behind |
|---------|-------------|-------------------|----------------|-------------|
| agents/overview.md | 2026-03-15 | internal/agent/domain.go | 2026-04-10 | 26 |

## Summary
Total articles: N | Stale: N | Fresh: N
```

</flows>
