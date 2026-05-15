---
description: Start new forge run (greenfield or refactor). Triage gate picks path, runs Phase 1 (Perspective), hands off to /forge:scaffold.
argument-hint: [--new | --fix] <description>
allowed-tools: [Bash, Read, Write, Edit, Agent, AskUserQuestion, Glob, Grep]
---

# /forge:new

Entry point. Triage gate → Phase 1 → hand off to `/forge:scaffold`.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/pipeline/SKILL.md` for stage contracts and artifact schemas.

## Triage

Parse `$ARGUMENTS`:

- `--new <desc>` → greenfield path (dual interrogation, parallel research, PRD, designer)
- `--fix <desc>` → refactor path (blast-radius-mapper, abbreviated interview, PRD, designer)
- No flag → AskUserQuestion to pick

## Init State

```bash
mkdir -p .forge/{contracts,reviews,interview,research}
[ -f .forge/prd.json ] || echo '{"version":1,"feature":"","created":"'$(date -Iseconds)'","tasks":[]}' > .forge/prd.json
[ -f .forge/anti-cheat.yaml ] || cat > .forge/anti-cheat.yaml <<'YAML'
# Forge anti-cheat allowlist
# Each entry: pattern (one of NOT_IMPLEMENTED, EMPTY_BODY, SKIPPED_TEST,
# HARDCODED_FAKE, MOCK_IN_PROD, TODO_MARKER, MAGIC_OK), optional paths globs,
# optional expires_at (ISO date).
allowlist: []
YAML
grep -qxF '.forge/' .gitignore 2>/dev/null || echo '.forge/' >> .gitignore
```

## Greenfield Path (`--new`)

### Stage 1: Dual Interrogation

Sequentially (user can't answer two streams):
1. Agent `pm-interrogator` → `.forge/interview/pm.md`
2. Agent `design-interrogator` → `.forge/interview/design.md`

Both may call AskUserQuestion. Cap each at 5 rounds.

**Inter-stage review:** Agent `general-reviewer` → `.forge/reviews/01-interrogation.md`. On `block` → loop stage.

### Stage 2: Parallel Research

Dispatch in parallel (single message, two Agent calls):
- `context-researcher` → `.forge/research/context.md`
- `pattern-researcher` → `.forge/research/pattern.md`

**Inter-stage review** → `.forge/reviews/02-research.md`.

### Stage 3: PRD

Agent `prd-writer` → `.forge/prd.md`.

**Inter-stage review** → `.forge/reviews/03-prd.md`.

### Stage 4: Technical Design

Agent `technical-designer` → `.forge/shared.md`.

**Inter-stage review** → `.forge/reviews/04-design.md`.

## Refactor Path (`--fix`)

### Stage 1-alt: Blast Radius

Agent `blast-radius-mapper` → `.forge/blast-radius.json` + `.forge/blast-radius-full.txt`.

Single AskUserQuestion confirming fix description + flagging out-of-scope warning if present.

### Stage 2-alt: Restricted Research

Dispatch in parallel, BUT pass blast-radius file list as scope cap:
- `context-researcher` (restricted to listed files)
- `pattern-researcher` (restricted)

### Stage 3-4: same as greenfield

PRD writer prefilled with blast-radius scope. Technical designer treats `shared.md` as a *delta* over existing arch, not full design.

## Stage 5: Human Gate (both paths)

AskUserQuestion with `shared.md` summary in `preview` field. Options:
- `approve` → hand off to `/forge:scaffold`
- `revise` → loop technical-designer with user feedback
- `abort` → exit; leave `.forge/` for inspection

## Graph rebuild (after Phase 1)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" rebuild
```

Indexes prd.md, shared.md, interviews, research, reviews into the spec graph. Phase 2 agents will query it instead of re-reading whole files.

Also recommended: rebuild after each Phase 1 stage if iterating (the build is sub-second).

## Hand-off

On approve, instruct user (or auto-invoke if session permits):

```
Phase 1 complete. shared.md approved. Graph indexed.
Next: /forge:scaffold
```

## Report

Per stage: agent dispatched, artifact written, review verdict. End with phase status + next command.
