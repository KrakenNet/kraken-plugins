---
name: graph
description: Spec graph layer for forge. SQLite-backed index over Phase 1 artifacts (prd.md, shared.md, interviews, research, reviews) + Phase 2 task array (prd.json) + outcome edges from Ralph Loop. Agents query graph instead of re-reading whole files for 5-10x token reduction.
---

# Forge Graph

Spec + outcome graph. Code indexing deferred to v0.3.

## Why

Subagent reading prd.md (5k) + shared.md (8k) + interview/design.md (4k) = 17k tokens of context, mostly redundant. Graph query returns 1-2k tokens of focused bullets w/ cites. Subagent opens specific lines only when needed.

Stack with caching: stable graph context (cached prefix) + task-specific delta (fresh).

## Schema

**Nodes:**

| kind | source | what it represents |
|---|---|---|
| spec_ac | prd.md "Acceptance criteria" | testable assertion |
| story | prd.md "User stories" | as-a/I-want/so-that |
| risk | prd.md, shared.md "Risks" | known hazard |
| open_question | prd.md, interviews | unresolved |
| journey | interview/design.md | user flow step |
| state | interview/design.md | empty/loading/error/success |
| component | shared.md "Components" | named module |
| interface | shared.md "Interfaces" | typed signature |
| decision | scope/dependencies/data-flow/build-sequence/UX | locked choice |
| reuse_candidate | research/{context,pattern}.md | existing thing to reuse |
| file | shared.md file plan + prd.json files | path on disk |
| task_run | prd.json + Ralph outcomes | one task in the run |
| gate_event | Ralph Loop attempts | static/anti-cheat/test/adversarial fire |
| blocker | Ralph stuck states | resolution recipes link here |
| pattern | learned subgraphs | reusable playbooks |

**Edges (typed):**

`covers`, `depends_on`, `cites`, `conflicts_with`, `implements`, `mentions`,
`contains`, `instance_of`, `touched`, `fired_gate`, `blocked_by`, `resolved_by`,
`similar_to`, `uses_pattern`.

## Build

`scripts/graph_build.py` parses spec markdown by headings + bullets. Heading text classifies node kind (e.g. "Acceptance criteria" → spec_ac children).

Build is idempotent. Run after every Phase 1 stage and after scaffold. Cheap (sub-second).

Files remain authoritative. Graph is a derived index — can always rebuild from source. If graph and files disagree, files win; rebuild.

## Query CLI

```bash
forge-graph context-for-task <id> --max-tokens 2000
  -> task node + covered ACs + implementing components +
     files in scope + decisions + prior outcomes on same files

forge-graph query "<keyword>" --max-tokens 1500
  -> LIKE search across title/body/tags

forge-graph open-questions [--topic X]
  -> all unresolved questions, optionally topic-filtered

forge-graph status
  -> node/edge counts by kind/rel
```

## How agents use this

**Pre-task (ralph-coder, code-simplifier):**

```bash
forge-graph context-for-task <task-id> --max-tokens 2000
```

Returns markdown bullets. Internalize. Only Read source files cited if absolutely necessary (use offset/limit).

**During Phase 1 (pm-interrogator, design-interrogator):**

```bash
forge-graph query "<topic>" --kind decision
forge-graph open-questions
```

Avoid asking the user something already decided. Surface open questions instead of inventing new ones.

**Post-task (ralph-coder, lessons-keeper):**

```bash
forge-graph record-outcome --task-id X --status passed \
  --files src/a.ts,src/b.ts --gates static:pass,anti-cheat:pass,test:pass,adversarial:pass
```

Adds task_run + touched + fired_gate edges. Future queries on same files surface this run as "prior outcome."

## Fidelity check

A graph that loses 30% of decisions is worse than reading the file. Validate:

```bash
forge-graph status   # node counts should match rough header counts in source
```

If sections are missing or wrong kind: open `scripts/graph_build.py`, adjust
`heading_kind()`. Rebuild.

## Graphify integration

```bash
forge-graph export-graphify --out .forge/memory/graph-export.jsonl
```

Emits node/edge JSONL. Pipe to user's `/graphify` for visualization or
cross-project knowledge pool. Forge does NOT depend on graphify at runtime —
export is one-way.

## What's NOT in v0.2

- Code indexing (symbols, imports, tests). Deferred to v0.3 pending
  measurement of spec-only savings.
- Embeddings. Current similarity = keyword + path-overlap. Good enough below
  N=50 task_runs. Upgrade later.
- Cross-project memory pool. Per-repo `.forge/memory/graph.db` for now.

## Pitfalls

- **Stale graph** — if you edit prd.md and forget to rebuild, queries lie.
  Run `forge-graph rebuild` after every spec edit. Consider a PostToolUse
  hook for `.forge/*.md` writes (not added by default to avoid hook bloat).
- **Heading drift** — if PRD or shared.md use non-conventional headings,
  `heading_kind()` falls back to "decision". Stick to the templates.
- **Over-trust** — graph bullets are *summaries*. For interface signatures or
  acceptance assertions, Read the cited file:line. Don't paraphrase off the
  bullet alone.
