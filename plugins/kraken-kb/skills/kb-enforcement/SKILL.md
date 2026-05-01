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

| Path Pattern | Domain | Sub-articles to consider |
|---|---|---|
| `internal/agent/` (excluding `tool_executor.go`, `pipeline/`) | agents | overview, looping, budget, enrichers, interceptors, demonstrations, optimizers, skills, chat |
| `internal/agent/modules/` | agents/modules | modules/overview + modules/<name> for the specific module touched |
| `internal/agent/tool_executor.go`, `internal/agent/pipeline/` | tools | overview |
| `internal/governor/` | governors | overview |
| `internal/workflow/`, `internal/workflow/engine/` | workflows | overview, execution, human-in-the-loop, requests/, steps/ |
| `internal/rag/`, `internal/retrieval/` | knowledge | overview, rag/, knowledge-bases |
| `internal/knowledge/`, `internal/knowledgebase/` | knowledge | overview, knowledge-bases, access-control, knowledge-graphs/ |
| `internal/memory/` | knowledge | memories |
| `internal/integration/` | integrations | overview |
| `internal/gomlx/`, `internal/onnxrt/`, `internal/ml/` | machine-learning | overview, model-definitions, datasets, layers, training-runs, pre-trained-models, inference |
| `internal/credential/` | credentials | overview |
| `internal/compliance/` | compliance | overview |
| `internal/tracing/` | tracing | overview |
| `internal/platform/chat/` | chat | overview |
| `internal/platform/portals/`, `web-*-ui/src/pages/` | portals | overview + page-specific |
| `web-dev-ui/src/pages/<X>/` | map page directory name to domain | — |
| `supabase/volumes/db/init/` | schema | cross-reference migration filename |
| `internal/api/` | platform | overview |
| `cmd/server/` | platform | overview |

If no domain can be determined, skip enforcement silently.

## Step 2: Load Articles

1. Read `docs/_index.md`
2. Find the routing section(s) that match the detected domain(s) and task description
3. Read each listed article

## Step 2.5: Module-Aware Routing

If the changed file is under `internal/agent/modules/<module>/`, also load `docs/agents/modules/<module>.md` if present. If the file references a specific DSPy module type (predict, chain_of_thought, react, etc.) that the diff/PR changes, prefer that module's article over the generic overview.

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
