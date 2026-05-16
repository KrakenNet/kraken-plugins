# Forge Plugin — Open Proposals

Tracked design changes / fixes for the forge plugin. Each entry: motivation,
proposed change, files involved, risk notes.

---

## P1 — State-derived anti-cheat allowlist (replace wildcard NOT_IMPLEMENTED entries)

**Filed:** 2026-05-15
**Reporter:** sean / Context Distiller build
**Severity:** medium (silent cheat passthrough)
**Status:** open

### Motivation

In the Context Distiller forge run (`~/leagues/uaist-test/uaist/`), Phase 2
closed with `42/42 tasks pass` and `anti-cheat-scan exit 0`, yet operator
audit found three real stubs still in production paths:

1. `models/export_intent_clf.py` — `raise NotImplementedError("scaffolded stub: ...")`
2. `eval/run_eval.py` — `return 1` hardcoded; no bake-off
3. `context_distiller/cli/__main__.py` — `explain` subcommand renders a
   placeholder string referencing a non-existent task ("T22-harbor-explain")

All three passed because `.forge/anti-cheat.yaml` carried blanket Phase 2
allowlist entries written by `skeleton-scaffolder`:

```yaml
- pattern: NOT_IMPLEMENTED
  paths:
    - context-distiller/context_distiller/nodes/*.py
    - context-distiller/context_distiller/adapters/*.py
    - context-distiller/context_distiller/serve/*.py
    - context-distiller/context_distiller/cli/*.py
    - context-distiller/eval/run_eval.py
    - context-distiller/eval/judge.py
    - context-distiller/eval/report.py
    - context-distiller/eval/baselines/*.py
    - context-distiller/eval/datasets/*/loader.py
    - context-distiller/models/export_intent_clf.py
    # …~20 paths total
  expires_at: "2026-06-15"
  reason: "Phase 2 scaffold stubs"
```

The wildcard globs are correct at scaffold time — every file genuinely is
a stub. The bug is that **no pipeline stage re-narrows the allowlist as
`ralph-coder` fills in stubs**. The `expires_at` field is a 30-day time
bomb, not a state check.

### Root cause

Scaffolder lists every generated stub path in the allowlist. Ralph-coder
commits real implementations without touching `anti-cheat.yaml`. Files
covered by the wildcards keep passing the anti-cheat scan whether they
contain real code or unchanged stubs — the scan only asks "does the
pattern appear in a non-allowlisted path?"

### Proposed change (Option 4 — state-derived allowlist)

Replace human-managed wildcard allowlist with a SHA-based state file
the scaffolder writes once and the anti-cheat scan checks every call:

1. **`forge:skeleton-scaffolder`** writes `.forge/scaffolded-stubs.json` on
   stub generation:

   ```json
   {
     "scaffolded_at": "2026-05-15T16:51:25Z",
     "stubs": [
       {
         "path": "context-distiller/models/export_intent_clf.py",
         "stub_sha256": "abc123…",
         "pattern": "NOT_IMPLEMENTED",
         "task": "T09-versions-manifest"
       },
       …
     ]
   }
   ```

   Each entry records the SHA-256 of the file *as scaffolded*. The plain
   `anti-cheat.yaml` `allowlist:` field is reserved for genuinely human-
   approved exceptions (e.g. legitimately-empty fallback classes, deferred
   Phase 3 work).

2. **`scripts/anti_cheat_scan.py`** changes its allowlist lookup:

   - For a hit at `<path>` matching `<pattern>`:
     - If `<path>` appears in `scaffolded-stubs.json` AND the file's current
       SHA-256 == the recorded `stub_sha256` → still a stub → allow.
     - If `<path>` appears in the JSON but current SHA-256 ≠ recorded SHA-256
       → file was modified → **the allowlist for this path auto-expires**.
       The hit now fails the scan.
     - Else fall back to the existing `allowlist:` field in
       `anti-cheat.yaml` (for human-approved deferred work).

3. **`forge:status`** gains a "stale stubs" line:

   ```
   === Anti-cheat state ===
     scaffolded stubs:   24 total
       still stub:       2  (eval/run_eval.py, cli/__main__.py)
       filled in:        22
       stale allowlist:  0   (path no longer matches recorded SHA)
   ```

   Surfaces drift in `/forge:status` so operators see anti-cheat health
   without needing a separate audit.

4. **`forge:ralph-coder`** no longer needs to touch the allowlist on green —
   the SHA comparison handles it automatically. If the coder leaves the
   stub body intact (cheat), the SHA matches and the file stays allowlisted
   — but that's the cheat scaffolder-stage tests + adversarial gate already
   try to catch via behavioural assertions on the same file. Two layers of
   defence.

### Files to change

- `plugins/forge/agents/skeleton-scaffolder.md` — add the SHA-emit step;
  document the contract.
- `plugins/forge/scripts/anti_cheat_scan.py` (and/or `anti-cheat-scan.sh`)
  — implement the SHA-based lookup with fallback to the YAML allowlist.
- `plugins/forge/skills/pipeline/SKILL.md` — document the
  `.forge/scaffolded-stubs.json` artifact in the artifact catalogue.
- `plugins/forge/commands/status.md` (or wherever `/forge:status` lives) —
  add the anti-cheat state report.
- `plugins/forge/agents/ralph-coder.md` — remove (now stale) guidance about
  trimming the allowlist on green; instead document that filling in a stub
  body is sufficient.

### Migration / backwards compat

Existing runs without `.forge/scaffolded-stubs.json` keep using the legacy
YAML allowlist (no SHA file → no auto-expire layer). `/forge:status` can
print a one-line nag suggesting `/forge:scaffold` or a new
`/forge:rebuild-stub-manifest` command to backfill the JSON from `git log`
+ current file SHAs.

### Risks / open questions

- What if the operator legitimately re-formats a stub file (e.g. ruff
  auto-formatting changes the file SHA without filling in the stub)? The
  SHA mismatch then incorrectly fires anti-cheat. Mitigation: normalise the
  file (strip whitespace + comments) before SHA, OR record the AST hash of
  the function body instead of file-level SHA. Latter is more robust but
  language-specific.
- Adding SHA storage couples forge to file content; bin format changes
  (binary stubs, generated YAML) need a per-pattern hashing strategy.

### Out of scope (related but not this proposal)

- "Strict mode" flag on anti-cheat scan that ignores `expires_at` entirely
  (see P2 below).
- Per-task allowlist pruning by `ralph-coder` (P3 fallback if SHA approach
  proves brittle for some patterns).

---

## P2 — Strict-mode anti-cheat scan for CI / PR gate

**Filed:** 2026-05-15
**Reporter:** sean / Context Distiller build
**Severity:** medium (gate weakness — CI accepts time-bombed cheats)
**Status:** open
**Depends on:** P1 (uses the same `scaffolded-stubs.json`) but ships independently

### Motivation

`expires_at` on allowlist entries is a developer ergonomics affordance —
"this stub is OK during Phase 2, ping me again in 30 days." Useful locally
during the Ralph Loop. **Wrong for CI / pre-merge gates**: a PR that adds
new code while a stub is still time-allowlisted gets a green anti-cheat
scan, even though the stub IS still in production.

Today's `anti_cheat_scan.py` makes no distinction between "developer
running locally during scaffold" and "CI evaluating a candidate merge."
The same allowlist semantics apply to both.

### Proposed change

Add a `--strict` flag (and corresponding env var `FORGE_ANTI_CHEAT_STRICT=1`)
to `scripts/anti_cheat_scan.py` / `anti-cheat-scan.sh`:

- **Default (lenient) mode** — current behaviour. Allowlist entries honored
  with `expires_at` enforced. Used during local Ralph Loop and the
  PostToolUse hook.
- **Strict mode**:
  - `expires_at` is **ignored** — entry validity is purely state-derived.
  - Only entries that are *truly state-justified* allow a hit:
    - Per P1: file SHA still matches recorded scaffolded-stub SHA.
    - Per legacy YAML allowlist: reason must include a `STRICT_OK:` prefix
      to opt in (e.g. `STRICT_OK: Phase 3 work tracked in issue #42`).
  - All other hits — even ones inside the YAML allowlist with future
    `expires_at` — fail the scan.

### Where strict mode runs

1. **`/forge:init-ci`** generated GitHub Actions workflow runs the scan
   with `--strict` in the PR-time job. Local pre-commit hook stays lenient.
2. **`/forge:status`** prints a side-by-side "lenient: pass, strict: 3 hits"
   diagnostic so operators see what would break on a PR before they push.
3. **Phase 3 promotion gate** (whenever `/forge:init-ci` lands an E2E
   gauntlet) runs `--strict` as a prerequisite to invoking the bake-off
   eval — gates that promotion gate stays honest.

### Files to change

- `plugins/forge/scripts/anti_cheat_scan.py` — `--strict` flag, env var,
  STRICT_OK prefix handling.
- `plugins/forge/scripts/anti-cheat-scan.sh` — wrap-through.
- `plugins/forge/commands/init-ci.md` (or the actual workflow template)
  — invoke with `--strict` in the CI job, lenient in pre-commit.
- `plugins/forge/commands/status.md` — print both lenient + strict results.
- `plugins/forge/skills/pipeline/SKILL.md` — document the two-tier gate
  contract.

### Risks / open questions

- A noisy strict mode on day 1 will block every legitimate Phase 2 PR
  (since most files start as scaffolded stubs). Need a "Phase 2 in
  progress" sentinel that suppresses strict in CI until `/forge:resume`
  reports `all green`. Possibly: strict mode is no-op if any task in
  `prd.json` has `passes: false`.
- `STRICT_OK:` prefix bikeshed — alternatives: a separate
  `strict_allowlist:` block, or a `severity: strict-bypass` field per
  entry. Picking the prefix because it's grep-friendly + low schema churn.

### Out of scope

- Auto-removing expired entries from `anti-cheat.yaml` (housekeeping
  command; separate trivial proposal).
- Cross-repo anti-cheat (currently scoped to a single forge project).
