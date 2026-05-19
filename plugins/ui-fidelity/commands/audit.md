---
description: Run full UI-fidelity audit (8 gates) on changed routes or given paths. Writes .ui-fidelity/report.{json,md}.
argument-hint: [--all | --routes <glob>...] [--skip-llm] [--budget <n>]
allowed-tools: [Bash, Read, Write, Edit, Agent, Glob, Grep]
---

# /ui-fidelity:audit

Multi-gate UI audit. Exits non-zero on any failure.

## Load skill

Read `${CLAUDE_PLUGIN_ROOT}/skills/ui-fidelity/SKILL.md` for gate contracts.

## Parse args

- `--all` → audit every route in `src/App.tsx`
- `--routes <glob>...` → audit matching files
- `--skip-llm` → skip gate 8 (cheap dev loop)
- `--budget <n>` → cap LLM critic to N route screenshots (default 10)
- No args → audit diff vs `main`

## Detect project

```bash
test -f package.json || { echo "no package.json"; exit 1; }
grep -q '"react"' package.json || echo "warn: not detected as React"
grep -q '"@playwright/test"' package.json || echo "warn: Playwright not installed — gates 1,2,4,7,8 will be skipped"
grep -q '"@axe-core/playwright"' package.json || echo "info: axe-core missing, will offer to install"
```

## Bootstrap `.ui-fidelity/`

If `.ui-fidelity/` missing, run scripts/bootstrap.mjs from `${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.mjs`. It creates config, empty allowlists, copies templates.

## Dispatch orchestrator

```
Agent({
  subagent_type: "ui-fidelity:audit-orchestrator",
  prompt: "Run audit. Targets: <list>. Skip-llm: <bool>. Budget: <n>. Read SKILL.md first. Spawn gate agents 1-7 in parallel. Aggregate findings. If 1-7 clean, run gate 8 within budget. Write .ui-fidelity/report.json and .md. Return pass/fail summary."
})
```

## Output

Print Markdown summary from `.ui-fidelity/report.md`. Exit 1 on any fail.
