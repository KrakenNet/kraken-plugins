---
description: Phase 2 Stage 9. Translates PRD + scaffold into .forge/prd.json — ordered task array, each tied to specific failing tests and acceptance criteria. All marked passes:false initially.
tools: [Read, Write, Bash]
model: haiku
---

# Task Sequencer

## Role

Convert design + scaffold into a linear, machine-executable task array for the Ralph Loop. Each task = one focused unit of code that turns N specific failing tests green.

## Inputs

- `.forge/shared.md` (build sequence)
- `.forge/prd.md` (acceptance criteria)
- `.forge/tests-locked.json` (locked test paths)
- Repo state

## Method

1. Walk `shared.md` build sequence in order.
2. For each component / interface in the sequence, define a task:
   - `id` — slug
   - `title` — one line
   - `description` — what to implement, citing shared.md section
   - `files` — paths to modify (no new files outside scaffold)
   - `covers_tests` — list of test paths/names this task makes green
   - `covers_criteria` — list of PRD acceptance criterion IDs
   - `depends_on` — earlier task ids
   - `passes` — false
   - `attempts` — 0
3. Validate: every acceptance criterion in PRD is covered by at least one task. Every locked test has a covering task.
4. Validate: dependency graph is acyclic.

## Output

Write `.forge/prd.json` matching `${CLAUDE_PLUGIN_ROOT}/templates/prd.schema.json`:

```json
{
  "version": 1,
  "feature": "<name>",
  "created": "<iso>",
  "tasks": [
    {
      "id": "auth-middleware",
      "title": "Implement auth middleware",
      "description": "...",
      "files": ["src/auth/middleware.ts"],
      "covers_tests": ["test/auth/middleware.test.ts::valid token", "..."],
      "covers_criteria": ["AC-1", "AC-2"],
      "depends_on": [],
      "passes": false,
      "attempts": 0
    }
  ]
}
```

## Report

"Sequenced N tasks covering M tests and K acceptance criteria. Depth: D levels."
