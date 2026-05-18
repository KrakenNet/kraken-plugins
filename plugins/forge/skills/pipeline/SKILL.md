---
name: pipeline
description: Foundation skill for forge. Defines 17-stage pipeline, artifact schemas, agent roster, gate contracts, and when each piece fires. Read by every forge command and agent at start.
---

# Forge Pipeline

The Ultimate AI Software Team, encoded.

## Phases at a glance

```
Phase 1 PERSPECTIVE   (humans + research, what to build)
   1. Dual Interrogation: pm-interrogator || design-interrogator
   2. Parallel Research:  context-researcher || pattern-researcher
   3. PRD Writer
   4. Technical Designer (shared.md)
   5. Human Gate
   [general-reviewer fires between every stage]

Phase 2 PROCESS        (local execution, how to build)
   6. Skeleton Scaffolder & TDD Enforcer
   7. Test Simplifier + lock tests
   8. Adversarial Contract Generator
   9. Task Sequencer (prd.json)
  10. Adversarial Ralph Loop:
        ralph-coder
          -> static gate
          -> anti-cheat gate
          -> architecture-fitness gate
          -> test gate
          -> adversarial sandbox
        (loop until prd.json all passes:true)
  11. Code Simplifier
  12. Atomic Commit & Push

Phase 3 ENVIRONMENT    (CI/CD, installed via /forge:init-ci)
  13. Standard CI + 13a. Auto-Fixer
  14. Ensemble Reviewers (security || performance || architecture)
  15. Full Adversarial E2E Gauntlet
  16. Specum Formatter (PR body)
  17. Draft PR
```

## Artifact map

```
.forge/
├── interview/
│   ├── pm.md             (pm-interrogator)
│   └── design.md         (design-interrogator)
├── research/
│   ├── context.md        (context-researcher)
│   └── pattern.md        (pattern-researcher)
├── prd.md                (prd-writer)
├── shared.md             (technical-designer)
├── tests-locked.json     (skeleton-scaffolder)
├── prd.json              (task-sequencer)   ← Ralph Loop's source of truth
├── contracts/            (contract-generator)
│   ├── *.spec.ts         (Playwright)
│   ├── *.postman.json
│   └── *.docker.sh
├── reviews/
│   ├── 01-interrogation.md
│   ├── 02-research.md
│   ├── 03-prd.md
│   └── 04-design.md
├── scaffolded-stubs.json (skeleton-scaffolder; SHA-keyed stub allowlist — auto-expires on edit)
├── anti-cheat.yaml       (legacy human-managed allowlist; STRICT_OK: prefix bypasses --strict)
├── architecture.yaml     (optional; thresholds for file_loc, function_loc, class_methods, fan_in)
├── baseline-metrics.json (blast-radius-mapper or manual; per-file pre-change metrics for differential gate)
├── architecture-exemptions.jsonl (append-only audit log of honored override comments)
└── blockers.md           (Ralph stuck state)
```

## Agent roster

| Agent | Phase | Stage | Trigger |
|---|---|---|---|
| pm-interrogator | 1 | 1 | /forge:new --new |
| design-interrogator | 1 | 1 | /forge:new --new |
| blast-radius-mapper | 1 | 1-alt | /forge:new --fix |
| context-researcher | 1 | 2 | /forge:new (parallel) |
| pattern-researcher | 1 | 2 | /forge:new (parallel) |
| prd-writer | 1 | 3 | /forge:new |
| technical-designer | 1 | 4 | /forge:new |
| general-reviewer | 1 | inter-stage | between every Phase 1 stage |
| skeleton-scaffolder | 2 | 6 | /forge:scaffold |
| contract-generator | 2 | 8 | /forge:scaffold |
| task-sequencer | 2 | 9 | /forge:scaffold |
| ralph-coder | 2 | 10 | /forge:resume, self-invoking |
| anti-cheat | 2 | gate | PostToolUse hook + Ralph gate + PR check |
| architecture-reviewer | 2 | gate 2.5 | PostToolUse hook + Ralph gate + PR check |
| code-simplifier | 2 | 11 | post Ralph Loop all-green |

## Gate contracts (Ralph Loop)

Order matters. Each gate has fail-fast semantics.

1. **Static gate** — empty diff fails. Project lint cmd must pass.
2. **Anti-cheat gate** — `scripts/anti-cheat-scan.sh full`. Exit non-zero on block-severity.
2.5. **Architecture-fitness gate** — `scripts/architecture-scan.sh full`. Blocks god objects, oversized functions, and high fan-in. Differential against `.forge/baseline-metrics.json` when present. Override via `# forge: architecture-exempt reason="..."` comment (logged to `.forge/architecture-exemptions.jsonl`). Strict mode requires `STRICT_OK:` prefix on override reason.
3. **Test gate** — task's `covers_tests` first, then full locked suite (regression).
4. **Adversarial sandbox** — runs `.forge/contracts/*` against built/served artifact.

All five must pass → mark task `passes:true`, atomic commit.

## prd.json schema

See `${CLAUDE_PLUGIN_ROOT}/templates/prd.schema.json`.

## Anti-cheat patterns

See `agents/anti-cheat.md`. Block-severity: NotImplementedError, vacuous returns in prod paths, skipped tests, mock-in-prod imports, hardcoded fake env values.

## Architecture-fitness patterns

See `agents/architecture-reviewer.md`. Block-severity: file LOC > threshold,
function LOC > threshold, class method count > threshold, fan-in (caller file
count) per symbol > threshold. Defaults in
`scripts/architecture_scan.py`; override per repo via `.forge/architecture.yaml`.

### Differential rule (refactor mode)

When `.forge/baseline-metrics.json` exists (captured by `blast-radius-mapper`
on refactor entry, or manually via `architecture-scan.sh baseline`):

- Was under, is over → BLOCK (regression).
- Was over, got worse → BLOCK (can't make bad worse).
- Was over, unchanged → WARN (legacy carry-over).
- Was over, improved → PASS.

This lets the gate fire on existing codebases without rejecting every legacy
god object on day 1.

### Override discipline

Mirrors anti-cheat's `STRICT_OK:` prefix pattern. Comment in file:

```
# forge: architecture-exempt reason="legacy auth shim — extraction tracked in T15"
```

Strict mode (CI) only honors `reason="STRICT_OK: ..."`. Every honored
override appends a JSONL entry to `.forge/architecture-exemptions.jsonl`.
Never auto-add overrides.

### Allowlist layering

Two sources, checked in order:

1. **`.forge/scaffolded-stubs.json`** — state-derived. Written once by
   `skeleton-scaffolder` with `{path, stub_sha256, pattern, task}` per stub.
   A hit is allowed iff the file's current SHA-256 still matches
   `stub_sha256`. Editing the file (filling in the body) auto-expires the
   entry — no human bookkeeping. Replaces wildcard glob allowlists.
2. **`.forge/anti-cheat.yaml`** — legacy human-managed. Reserved for
   genuinely deferred work (e.g. fallback classes, Phase 3 stubs). Honors
   `expires_at`. In **strict** mode (CI / PR gate), `expires_at` is ignored
   and only entries whose `reason:` begins with `STRICT_OK:` are honored.

Strict mode (`--strict` / `FORGE_ANTI_CHEAT_STRICT=1`) auto-degrades to
lenient if `.forge/prd.json` reports any task `passes:false` (Phase 2 in
flight). Local Ralph Loop + PostToolUse hook run lenient; CI runs strict.

Diagnostic: `bash scripts/anti-cheat-scan.sh stubs-state` prints stub
health counts; `/forge:status` includes this in its dashboard.

## Phase 3 = GitHub Actions

Phase 3 reviewers run as GitHub Actions jobs (not local agents). Install via `/forge:init-ci`. Template at `${CLAUDE_PLUGIN_ROOT}/templates/.github/workflows/forge-review.yml`.

## Triage

`--new` → full pipeline starting at Stage 1 (dual interrogation).
`--fix` → Stage 1-alt: `blast-radius-mapper` scopes change, single confirm AskUserQuestion, then restricted research → PRD (refactor framing) → technical-designer (treats `shared.md` as delta over existing arch).

Refactor path is materially different: no full interview, restricted context window, design output is a delta not a full architecture.

## Resume semantics

`/forge:resume` reads `prd.json`, picks first task with `passes:false` and no unmet `depends_on`, dispatches `ralph-coder`. Self-invokes via SendMessage until done or blocked. Max 3 attempts per task → blocker.

## Style anchors (from CLAUDE.md)

- Surgical changes only. No drive-by refactors.
- No abstractions for single-use code.
- Every UX decision via AskUserQuestion before code.
- Match existing repo conventions over personal preference.

## Performance Pack (token efficiency + self-improvement)

Four cheap, additive optimizations. All on by default. None require the graph layer.

### 1. Caching discipline

Anthropic API caches stable prefixes (5min TTL, 90% discount on cached portion).
For caching to actually hit, every agent invocation must put stable content first:

```
[stable]   skill SKILL.md  →  agent system prompt  →  shared.md  →  prd.md
[dynamic]  task spec  →  lessons context  →  recipes context  →  user msg
```

Agents follow this convention: read foundation skill first, then specs, then
inject dynamic context. Never prepend timestamps, run-ids, or per-attempt
variables before the stable foundation.

### 2. Reflexion lessons (`.forge/lessons.md`)

Append-only markdown bullets. Newest first. Capped at ~50 entries via prune.

After every Ralph task (pass or block), `lessons-keeper` (haiku) extracts 0-3
generalizable bullets. Future ralph-coder invocations read the relevant
subset via `scripts/lessons.py context --tags ... --max-tokens 800`.

```
- [anti-cheat,scaffold] NotImplementedError in src/scaffold/** is expected
  during Stage 6 — add allowlist entry on day 1
```

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py {add|list|prune|context}`.

### 3. Cheap-model triage

Per-agent `model:` frontmatter. Routing:

| Model | Agents | Why |
|---|---|---|
| haiku | general-reviewer, anti-cheat, architecture-reviewer, task-sequencer, blast-radius-mapper, lessons-keeper | classification, routing, mechanical extraction |
| sonnet (default) | ralph-coder, code-simplifier, contract-generator, skeleton-scaffolder, prd-writer, technical-designer, pm-interrogator, design-interrogator, context-researcher, pattern-researcher | code generation, design decisions, interview tact |
| opus | (none by default) | reserve for technical-designer on hard architectural calls if needed |

If the dispatcher's environment doesn't honor agent-level `model:`, fall back
to the parent session's model. Document this for adopters.

### 4. Failure recipe DB (`.forge/recipes.jsonl`)

Append-only JSONL. One recipe per past blocker resolution.

Schema: `category`, `symptom`, `resolution`, `task_id`, `files`, `occurred_at`,
`resolved_at`.

On any Ralph attempt failure, before retrying, ralph-coder calls:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py lookup "<gate symptom>" \
  --max 3 --max-tokens 800
```

Returns ranked similar past failures + what worked. Hybrid scoring: token
Jaccard + sequence ratio. No embeddings (cheap, no ML dep).

`lessons-keeper` adds new recipes when a blocker resolves.

### Combined effect

Realistic, measured over a 20-task feature:
- Caching: 30-50% token reduction on stable prefix re-reads
- Lessons + recipes: 0.3-0.5 fewer avg attempts per task by month 2
- Cheap-model triage: 5-10× cost reduction on routing/gating agents

Stack: 5-10× cheaper, 1.5-2× fewer attempts. Verify with measurements; don't
trust this estimate blindly.

### Future (NOT in this pack)

- GraphRAG over specs+code → biggest remaining win, but requires indexer
- Critic-actor pattern → another 1-2 LLM calls trade for fewer attempts
- DSPy prompt compilation → after N>50 runs, automate prompt distillation
