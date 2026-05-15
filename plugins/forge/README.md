# Forge

Ultimate AI software team. 17-stage pipeline encoded as a Claude Code plugin.

See `code-graph.md` (root inspiration) for full diagram.

## Commands

- `/forge:new` — start greenfield or refactor flow (triage gate)
- `/forge:resume` — re-enter Ralph Loop mid-task
- `/forge:status` — show `prd.json` task array state
- `/forge:init-ci` — install Phase 3 GitHub Actions workflow

## Pipeline

**Phase 1 — Perspective**

1. PM Interrogator **+** Design Interrogator (parallel dual interrogation)
2. Context Researcher **+** Pattern Researcher (parallel reuse + UX scan)
3. PRD Writer (spec-anchored constitution)
4. Technical Designer (`shared.md` w/ UX contract)
5. Human Gate (visual approval)

Inter-stage: `general-reviewer` sanity check between stages.

**Phase 2 — Process**

6. Skeleton Scaffolder & TDD Enforcer
7. Test Simplifier & Reviewer Gate
8. Adversarial Contract Generator (Playwright / Postman / Docker bash)
9. Task Sequencer (`prd.json`)
10. **Adversarial Ralph Loop** — coder → static gate → **anti-cheat gate** → test gate → adversarial sandbox
11. Code Simplifier
12. Atomic Commit & Push

**Phase 3 — Environment (GitHub Actions, installed via `/forge:init-ci`)**

13. Standard CI + Auto-Fixer
14. Parallel Ensemble Reviewers (security / performance / architecture)
15. Full Adversarial E2E Gauntlet
16. Specum Formatter (PR body)
17. Draft PR

## State

Per-project, gitignored:

```
.forge/
  prd.json            # task array, passes flags
  shared.md           # architectural contract + UX contract
  blast-radius.json   # refactor scope
  contracts/          # black-box adversarial suite
  reviews/            # inter-stage review notes
  anti-cheat.yaml     # stub/cheat allowlist
  interview/          # PM + Design transcripts
```

## Anti-Cheat

Hook fires on every Edit/Write. Scans for `TODO`, `NotImplementedError`, hardcoded fakes, skipped tests, mock leakage into prod paths. Blocks Ralph Loop commit if violation found outside allowlist.

## Performance Pack

Six cheap optimizations layered on top of the pipeline. See `skills/pipeline/SKILL.md` § Performance Pack and `skills/graph/SKILL.md`.

1. **Caching discipline** — stable prefix ordering in every agent for prompt cache hits.
2. **GraphRAG over specs** — SQLite spec graph; agents query focused bullets instead of re-reading whole prd.md/shared.md/etc. 5-10× context reduction.
3. **Critic agent** — cheap haiku pre-gate review of Ralph drafts. Catches obvious misreads before expensive gate cycles. Plan-before-code already in ralph-coder.
4. **Reflexion lessons** — `.forge/lessons.md`, `lessons-keeper` writes after every task, ralph-coder reads relevant bullets pre-attempt.
5. **Cheap-model triage** — haiku for routing/gating/critic, sonnet for code/design.
6. **Failure recipe DB** — `.forge/recipes.jsonl`, ralph-coder queries past resolutions on gate fail.

Commands: `/forge:graph`, `/forge:lessons`, `/forge:recipes`.
