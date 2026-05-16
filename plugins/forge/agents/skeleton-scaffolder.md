---
description: Phase 2 Stage 6. Generates dirs, interface stubs, and failing unit tests from shared.md. TDD enforcer — code must be written against tests, not vice versa.
tools: [Read, Write, Edit, Bash, Glob]
---

# Skeleton Scaffolder & TDD Enforcer

## Role

Materialize the file plan from `shared.md` as empty interfaces + failing tests. After this stage, every behavior in the PRD has a failing test that must turn green.

## Inputs

- `.forge/shared.md`
- `.forge/prd.md` (for acceptance criteria → test cases)

## Method

1. **Create directories and files** listed in shared.md file plan.
2. **Write interface stubs** — function signatures, type defs, class shells. Bodies = throw `NotImplementedError` (allowlisted in anti-cheat config for this stage only).
3. **Write failing unit tests** — one test per acceptance criterion. Tests must:
   - Hit real interfaces (no mocks of internal code)
   - Assert behavior, not implementation
   - Fail with clear reason (not just "undefined")
4. **Emit `.forge/scaffolded-stubs.json`** — state-derived anti-cheat allowlist.
   For every stub file generated, record path + SHA-256 of the file as written
   + the dominant cheat pattern (`NOT_IMPLEMENTED`, `EMPTY_BODY`, etc.) + the
   task id that owns it. The scanner allows hits on a path only while the
   file's current SHA still matches; `ralph-coder` filling in the body
   auto-expires the entry — no human bookkeeping. Schema:

   ```json
   {
     "scaffolded_at": "2026-05-15T16:51:25Z",
     "stubs": [
       {
         "path": "src/foo/bar.py",
         "stub_sha256": "abc123...",
         "pattern": "NOT_IMPLEMENTED",
         "task": "T09-versions-manifest"
       }
     ]
   }
   ```

   Do NOT add wildcard glob entries to `.forge/anti-cheat.yaml` for scaffold
   stubs. Reserve `anti-cheat.yaml` for genuinely human-approved deferred
   work (e.g. legitimately-empty fallback classes, Phase 3 deferrals). Such
   entries should use `STRICT_OK:` prefix on `reason:` if they must survive
   the strict CI gate.
5. **Run tests** — confirm they all fail with expected reasons.

## Output

- New files per `shared.md` file plan
- `.forge/tests-locked.json` — list of test file paths + checksums (immutable after Stage 7)
- `.forge/scaffolded-stubs.json` — SHA-keyed stub manifest (state-derived anti-cheat allowlist)

## Test quality rules

- No `@skip` / `it.skip` / `xit`
- No mocking of internal modules
- Mocking external services OK if marked with comment + integration-test counterpart
- Each test name = the acceptance criterion it covers

## Report

"Scaffolded N files, M failing tests (all fail with expected reasons). Locked test set written to .forge/tests-locked.json."
