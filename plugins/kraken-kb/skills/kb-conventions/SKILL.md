---
name: kb-conventions
description: Shared KB article format rules, frontmatter schema, line limits, gap file conventions, and _index.md routing format. Loaded by kb-writer, kb-auditor, and kb-linter agents for consistent output.
version: 1.0.0
user-invocable: false
---

# KB Conventions

Rules for Railyard Knowledge Base articles. All agents creating or validating KB content must follow these conventions.

## Project Paths

- KB root: `docs/` (relative to the railyard project root)
- Routing index: `docs/_index.md`
- Prompt templates: `docs/_prompts/` (do not modify)
- Gap files: alongside their parent article as `<name>-gaps.md`

## Article Frontmatter

Every article MUST have all 5 fields:

```yaml
---
domain: agents           # Which domain: agents, tools, governors, workflows, knowledge, integrations, ml, platform, portals
scope: overview           # What aspect: overview, execution, runtime, etc.
keywords: [agent, crud]   # Array of search terms
reads-before: [working on agent UI]  # Array of task descriptions this serves
depends-on: [platform/overview.md]   # Array of relative paths (from docs/) to related articles
---
```

## Required Sections

Every article MUST contain a `## Do Not` section listing explicit prohibitions for that domain.

## Line Limits

- Soft max: 200 lines — emit WARNING if exceeded
- Hard max: 300 lines — emit ERROR, article must be split

## Gap File Format

Gap files document known discrepancies between a KB article and the actual codebase.

- Filename: `<article-name>-gaps.md` (e.g., `overview-gaps.md` alongside `overview.md`)
- Same frontmatter structure, with `scope` suffixed `-gaps` (e.g., `scope: overview-gaps`)
- Each gap is a separate section:

```markdown
## Gap N: <Title>

<Description of the discrepancy>

**Impact**: <What breaks or misleads if this gap is not addressed>

### Fix

<How to resolve the gap>
```

## _index.md Routing Format

The routing index uses task-based sections:

```markdown
### <Task description>
- path/to/article1.md
- path/to/article2.md
```

Every article must appear in at least one routing entry. When creating or updating articles, add routing entries if missing.

## Domain Map

Maps file paths to KB domains for enforcement and article creation:

| Domain | Go Packages | Schema Files | Frontend Pages | KB Path |
|--------|------------|--------------|----------------|---------|
| agents | `internal/agent/` | `0010-agent_schema.sql` | `pages/agents/` | `docs/agents/` |
| tools | `internal/agent/tool_executor.go`, `internal/agent/pipeline/` | `0011-tool_schema.sql` | `pages/tools/` | `docs/tools/` |
| governors | `internal/governor/` | `0093-governor_schema.sql` | `pages/governors/` | `docs/governors/` |
| workflows | `internal/workflow/`, `internal/workflow/engine/` | `0094-workflow_schema.sql`, `0097-request_schema.sql` | `pages/workflows/` | `docs/workflows/` |
| knowledge | `internal/rag/`, `internal/knowledge/`, `internal/knowledgebase/`, `internal/memory/`, `internal/retrieval/` | `0096-rag_schema.sql`, `1000-knowledge_bases.sql` | `pages/documents/`, `knowledge-graph/`, `knowledge-bases/`, `memories/` | `docs/knowledge/` |
| integrations | `internal/integration/` | `0009-integration_schema.sql` | `pages/integrations/` | `docs/integrations/` |
| ml | `internal/gomlx/`, `internal/onnxrt/` | `0101-ml_gomlx_schema.sql` | `pages/models/`, `training/`, `trained-models/`, `datasets/` | `docs/machine-learning/` |
| credentials | `internal/credential/` | `0008-credentials.sql` | `pages/credentials/` | `docs/platform/credentials.md` |
| compliance | `internal/compliance/` | compliance migrations | `pages/compliance/` | `docs/platform/compliance.md` |
| tracing | `internal/tracing/` | `0095-trace_spans_schema.sql` | `pages/traces/` | `docs/platform/tracing.md` |
| chat | `internal/platform/chat/` | `0098-chat_schema.sql` | `pages/chat/`, `chatbots/` | `docs/agents/chat.md` |

## Source File Reference

Used by update and audit commands to find authoritative source code:

| Domain | Schema Files | Go Packages | Frontend Pages |
|--------|-------------|-------------|----------------|
| Platform | All `supabase/volumes/db/init/*.sql`, `internal/api/router.go`, `internal/api/responses.go` | `internal/api/` | `web-dev-ui/src/components/ui/` |
| Agents | `0010-agent_schema.sql`, `0012-agent-module-config.sql`, `0013-optimization_runs.sql`, `0014-agent-metadata.sql` | `internal/agent/` | `web-dev-ui/src/pages/agents/` |
| Tools | `0011-tool_schema.sql`, `0101-smart_tool_registry.sql` | `internal/agent/tool_executor.go`, `internal/agent/pipeline/` | `web-dev-ui/src/pages/tools/`, `pipelines/` |
| Governors | `0093-governor_schema.sql` | `internal/governor/` | `web-dev-ui/src/pages/governors/` |
| Workflows | `0094-workflow_schema.sql`, `0097-request_schema.sql`, `0099_alert_escalation.sql` | `internal/workflow/`, `internal/workflow/engine/` | `web-dev-ui/src/pages/workflows/` |
| Knowledge | `0096-rag_schema.sql`, `1000-knowledge_bases.sql` | `internal/rag/`, `internal/knowledge/`, `internal/knowledgebase/`, `internal/memory/`, `internal/retrieval/` | `web-dev-ui/src/pages/documents/`, `knowledge-graph/`, `knowledge-bases/`, `memories/` |
| Integrations | `0009-integration_schema.sql` | `internal/integration/` | `web-dev-ui/src/pages/integrations/` |
| ML | `0101-ml_gomlx_schema.sql`, `0093-training_schema.sql` | `internal/gomlx/`, `internal/onnxrt/` | `web-dev-ui/src/pages/datasets/`, `training/` |
