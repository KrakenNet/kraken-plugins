---
name: kb-enforcement
description: Auto-triggers on code modification tasks to load relevant KB articles, check gap files, and warn about staleness. Fires when modifying files under railyard/internal/, railyard/web-dev-ui/, railyard/web-admin-ui/, railyard/web-user-ui/, supabase/, or railyard/cmd/. Does NOT fire for docs-only changes, plugin work, or config files.
version: 1.0.0
user-invocable: false
---

# KB Enforcement

Automatically load relevant KB articles and warn about staleness before any code modification task.

## When This Skill Fires

This skill activates when the task involves modifying files under:
- `railyard/internal/`
- `railyard/web-dev-ui/`
- `railyard/web-admin-ui/`
- `railyard/web-user-ui/`
- `supabase/`
- `railyard/cmd/`

Do NOT activate for: docs-only changes, plugin work, config-only changes, or non-railyard repos.

## Step 1: Detect Domains

Identify which domain(s) the task touches by mapping file paths:

| Path Pattern | Domain |
|---|---|
| `internal/agent/` (excluding `tool_executor.go`, `pipeline/`) | agents |
| `internal/agent/tool_executor.go`, `internal/agent/pipeline/` | tools |
| `internal/governor/` | governors |
| `internal/workflow/`, `internal/workflow/engine/` | workflows |
| `internal/rag/`, `internal/knowledge/`, `internal/knowledgebase/`, `internal/memory/`, `internal/retrieval/` | knowledge |
| `internal/integration/` | integrations |
| `internal/gomlx/`, `internal/onnxrt/` | ml |
| `internal/credential/` | credentials |
| `internal/compliance/` | compliance |
| `internal/tracing/` | tracing |
| `internal/platform/chat/` | chat |
| `web-dev-ui/src/pages/<X>/` | map page directory name to domain |
| `supabase/volumes/db/init/` | schema — cross-reference migration filename (e.g., `0010` → agents) |
| `internal/api/` | platform |
| `cmd/server/` | platform |

If no domain can be determined, skip enforcement silently.

## Step 2: Load Articles

1. Read `docs/_index.md`
2. Find the routing section(s) that match the detected domain(s) and task description
3. Read each listed article

## Step 3: Check Gap Files

For each loaded article at path `docs/<domain>/<name>.md`:
1. Check if `docs/<domain>/<name>-gaps.md` exists
2. If it exists, read it and note the gaps

## Step 4: Staleness Check

For each loaded article:
1. Parse the `depends-on` field from the article's YAML frontmatter
2. For each dependency path, resolve it relative to `docs/`
3. Get the article's last-modified time:
   ```bash
   git log -1 --format=%ct -- docs/<article-path>
   ```
4. Get each dependency's last-modified time:
   ```bash
   git log -1 --format=%ct -- docs/<dep-path>
   ```
   Note: `depends-on` lists other KB articles, not source files. For source file staleness, check the domain's source files from the domain map:
   ```bash
   git log -1 --format=%ct -- <source-file-path>
   ```
5. Compare: if any source file was modified more recently than the article, mark as stale

## Step 5: Report

Present findings to the conversation context:

**If gaps found:**
> **KB Gaps for `<domain>`:** `<article>` has N known gaps. Key issues: <gap titles>

**If stale articles found:**
> **Stale KB Warning:** `<article>` may be outdated — `<source-file>` changed on <date> (article last updated <date>)

**Always present:**
> **KB Context Loaded:** Read N articles for domain(s): <list>. Key constraints: <"Do Not" items and critical rules from loaded articles>

## Behavior Rules

- This skill does NOT block work. It loads context and warns.
- Run once at task start, not on every file edit within the task.
- If the user acknowledges a staleness warning, do not repeat it.
- Do not load articles outside the detected domain(s) — trust the routing index.
