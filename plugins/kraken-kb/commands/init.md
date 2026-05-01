---
description: Bootstrap a Railyard-style Knowledge Base in the current project — scan structure, create docs layout, routing index, and skeleton articles
argument-hint: [--quick]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Agent]
---

# KB Init

Bootstrap a Knowledge Base for the current project using Railyard conventions.

## Scan Project Structure

Discover domains by scanning the project:

```bash
# Go packages
ls -d internal/*/ 2>/dev/null | sed 's|internal/||;s|/||'

# SQL migrations
ls supabase/volumes/db/init/*.sql 2>/dev/null | head -20

# Frontend pages
ls -d web-*/src/pages/*/ 2>/dev/null | sed 's|.*/pages/||;s|/||'
```

Map discovered directories to domains using the domain map in kb-conventions skill. For each directory found, build a domain entry with: name, go_packages, schema_files, frontend_pages, kb_path.

## Check for Existing KB

```bash
test -d docs/ && echo "EXISTS" || echo "NEW"
```

If EXISTS: warn "A docs/ directory already exists. This will add missing files but not overwrite existing ones. Continue?" (skip warning in --quick mode)

## Parse Arguments

From `$ARGUMENTS`:
- **--quick**: autonomous mode — include all discovered domains, create skeleton articles, no questions

## Route by Mode

### Interactive (default)

Ask these questions one at a time:

1. **"I found these domains: <list>. Include all of them?"**
   Let the user remove or add domains.

2. **"Any additional domains or custom directories to cover?"**
   Free-form. Optional.

3. **"Should I create skeleton articles (headers only, fast) or full articles (reads source code, slower)?"**
   Options: skeleton (default), full

### Quick (--quick)

1. Include all discovered domains
2. Mode = skeleton

## Delegate

Delegate to `kb-bootstrapper` agent via Agent tool with:
- domains: the domain list with source file mappings
- mode: skeleton | full
- project_root: current working directory

## Report

Show the agent's output: what files were created, total count, next steps.
Suggest: "Run `/kb:audit` to find remaining coverage gaps, or `/kb:new <domain/scope>` to add articles."
