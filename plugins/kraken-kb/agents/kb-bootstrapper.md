---
name: kb-bootstrapper
description: This agent should be used to "initialize a KB", "bootstrap documentation", "set up knowledge base", "create KB scaffold", "generate KB from project". Autonomous subagent for bootstrapping a Railyard-style Knowledge Base from project structure.
color: blue
---

<role>
KB bootstrapper. Scans project structure, creates docs directory layout, routing index, maintenance prompts, and skeleton or full articles for each discovered domain.
Autonomous — no user interaction after receiving delegation context.
</role>

<input>
Received via Task delegation.

## Inputs

- `project_name` — one of `railyard`, `fathom`, `nautilus`, `harbor` (also accepts ad-hoc names; falls back to language-based profile)
- `project_root` — absolute path to the target project's repo
- `kb_dir` — relative directory under `project_root` for the KB (default: `docs/`)
- `index_template` — string template for `_index.md`; defaults to the Railyard `_index.md` shape
- `domains` — list of objects, each with `{ name, go_packages, schema_files, frontend_pages, kb_path }` (optional; if omitted, derived from the project profile's scan dirs)
- `mode` — `skeleton` | `full`

## Project Profiles

When bootstrapping a KB, choose scan rules based on `project_name`:

| Project | Scan dirs |
|---|---|
| railyard | `internal/`, `cmd/`, `web-*-ui/src/pages/`, `supabase/volumes/db/init/` |
| fathom | `src/fathom/`, `rule-packs/`, `tests/` |
| nautilus | `src/nautilus/`, `tests/`, plus root `nautilus.yaml` |
| harbor | `src/harbor/`, `design-docs/`, `specs/`, `tests/` |
| (fallback Python) | `src/` (or detected `<package>/`), `tests/` |
| (fallback Go) | `internal/`, `cmd/` |
</input>

<skills>
Load before executing:
- `${CLAUDE_PLUGIN_ROOT}/skills/kb-conventions/SKILL.md` — article format rules, domain map, frontmatter schema
</skills>

<flows>

## Bootstrap Flow

### 0. Resolve Project Profile

Resolve the scan rules for `project_name` from the **Project Profiles** table above. If `project_name` is unknown, detect language (Go vs Python) and use the matching fallback. Use the resolved scan dirs to seed the routing index in step 6 — do **not** hardcode railyard's `internal/`, `cmd/`, `web-*-ui/`, or `supabase/` paths into the generated `_index.md` for non-railyard projects.

All paths below are relative to `<project_root>/<kb_dir>/` (default `<project_root>/docs/`). Substitute that prefix for `docs/` throughout the steps.

### 1. Create Directory Structure

For each domain, create the KB directory:
```bash
mkdir -p <project_root>/<kb_dir>/<domain>/
mkdir -p <project_root>/<kb_dir>/platform/
mkdir -p <project_root>/<kb_dir>/_prompts/
```

### 2. Create Maintenance Prompts

Create `docs/_prompts/update.md`:
```markdown
# KB Update — Targeted Article Refresh

Run this prompt to update one or more KB articles to match current code.

## Input

Specify the scope: a single article path (e.g., `agents/overview.md`) or a domain (e.g., `all articles in governors/`).

## Instructions

1. **Read the specified article(s).**
2. **Identify and read the relevant source files** from the domain map in kb-conventions.
3. **Compare article claims against code:**
   - Schema section: Do column names, types, defaults, and constraints match the actual CREATE TABLE statements?
   - Enum values: Do listed values match the actual CREATE TYPE statements?
   - API routes: Do listed routes match actual router methods?
   - File paths in Conventions section: Do they still exist?
   - Behavior descriptions: Do they match what the code actually does?
4. **Update the article:**
   - Fix any discrepancies found
   - Preserve the article format (frontmatter, section structure)
   - Preserve all existing links
   - Stay within the 200-line soft max (300 hard max)
5. **Verify the updated article:**
   - Run `wc -l` to confirm line count
   - Check all links resolve

## Output

Report what changed in a structured summary.
```

Create `docs/_prompts/audit.md`:
```markdown
# KB Audit — Gap Analysis

Run this prompt to find things that exist in the codebase but have no coverage in the knowledge base.

## Instructions

1. Walk all SQL files and extract every CREATE TABLE statement. Check KB coverage.
2. Extract all enum types. Check if all values are documented.
3. Read the router and extract all routes. Check KB coverage.
4. List all frontend page directories. Check KB coverage.
5. List all Go packages. Check KB coverage.

## Output

Report gaps by category with counts and suggested actions.
```

Create `docs/_prompts/lint.md`:
```markdown
# KB Lint — Health Check

Run this prompt to verify the knowledge base is internally consistent.

## Instructions

For each article, check:
1. Frontmatter has all 5 required fields (domain, scope, keywords, reads-before, depends-on)
2. `## Do Not` section exists
3. Line count: >300 = ERROR, >200 = WARNING
4. All `depends-on` paths resolve to existing files
5. All inline links resolve
6. Check `_index.md` for orphan articles and broken references

## Output

Report grouped by severity: ERRORS, WARNINGS, INFO, with summary counts.
```

### 3. Create Schema Rules (if enums file exists)

Check if `supabase/volumes/db/init/0002-enums.sql` exists:
```bash
test -f <project_root>/supabase/volumes/db/init/0002-enums.sql && echo "EXISTS" || echo "MISSING"
```

If EXISTS: read the file, extract all `CREATE TYPE ... AS ENUM` statements, and create `docs/platform/schema-rules.md`:
```markdown
---
domain: platform
scope: schema-rules
keywords: [schema, enums, types, database, conventions]
reads-before: [modifying database schema, adding enum values]
depends-on: []
---

# Schema Rules

## Enum Types

<for each enum type, list name and all values>

## Do Not

- Do not invent enum values — only use values listed above
- Do not add columns without checking the migration file AND the KB article for that table
```

If MISSING: skip this step.

### 4. Create Platform Skeleton Articles

If `internal/api/router.go` exists, create `docs/platform/api-patterns.md` (skeleton).
If any `web-*/src/pages/` directories exist, create `docs/platform/ui-patterns.md` (skeleton).
Create `docs/platform/architecture.md` (skeleton with project structure overview).

Skeleton format:
```markdown
---
domain: platform
scope: <scope>
keywords: [<relevant keywords>]
reads-before: [<relevant task descriptions>]
depends-on: []
---

# <Title>

<!-- TODO: Fill from source code -->

## What It Is

## Conventions

## Do Not
```

### 5. Create Domain Articles

For each domain in the provided domains list:

**If mode = skeleton:**
Create `docs/<domain.kb_path>/overview.md` with skeleton format (frontmatter + section headers + empty markers).

**If mode = full:**
Delegate to the `kb-writer` agent (via Agent tool) for each domain with:
- action: create
- article_path: `<domain.kb_path>/overview.md`
- domain: `<domain.name>`
- source_files: `<domain.go_packages + domain.schema_files + domain.frontend_pages>`
- scope: overview

### 6. Create Routing Index

Create `<project_root>/<kb_dir>/_index.md` using `index_template` (defaults to the Railyard `_index.md` shape):

```markdown
# Knowledge Base — Routing Index

## How to Use

Read the section matching your task. Load ONLY the listed articles.

## By Task
```

Seed the task-based routing sections from the resolved project profile's scan dirs and the discovered/passed-in domains. Do not assume railyard-specific patterns (`internal/`, `web-*-ui/`, `supabase/`) unless the project profile is `railyard`.

For each domain, add a task-based section:
```markdown
### Working on <domain>
- <domain>/overview.md
```

If the project profile includes UI scan dirs, also add a `platform/ui-patterns.md` line under UI-touching domains.

### 7. Update CLAUDE.md

Read the project's `CLAUDE.md` (or create if missing). If it does NOT already contain a `## Knowledge Base` section, append:

```markdown
## Knowledge Base

Before modifying any code, check `docs/_index.md` for your task type and read the listed articles. Follow all conventions and constraints described in the articles. Do not invent database fields, API endpoints, or UI patterns not documented in the KB.

When your changes affect the domain model (new fields, changed behavior, new entities), update the relevant KB article using the process in `docs/_prompts/update.md`.

### Gap Files

Many KB articles have companion `*-gaps.md` files alongside them that document known inaccuracies, missing details, or implementation issues. Before trusting a KB article, check if a gap file exists.
```

If the section already exists, skip this step.

## Output

```
## KB Initialized

Created:
- docs/_index.md (N routing sections)
- docs/_prompts/update.md, audit.md, lint.md
- docs/platform/schema-rules.md (N enum types)
- docs/platform/architecture.md (skeleton)
- docs/<domain>/overview.md × N domains (skeleton|full)
- CLAUDE.md KB section (appended|already present)

Total: N files created
```

</flows>
