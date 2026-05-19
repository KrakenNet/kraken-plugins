---
description: Run persona-journey Playwright suite. Each persona has a narrative spec under tests/persona/<persona>.spec.ts.
argument-hint: [<persona> | --all] [--headed]
allowed-tools: [Bash, Read, Glob, Agent]
---

# /ui-fidelity:persona

Run scripted persona journeys.

## Args

- `<persona>` → run one persona's spec
- `--all` → run every spec under `tests/persona/`
- `--headed` → run with a visible browser (debug)

## Process

1. Verify `@playwright/test` installed
2. Ensure dev server target. If `playwright.config.ts` declares `webServer`, use it. Else require `PLAYWRIGHT_BASE_URL`.
3. Run:
   ```bash
   pnpm exec playwright test tests/persona/<persona>.spec.ts ${HEADED:+--headed}
   ```
4. On failure, dispatch `ui-fidelity:persona-journey-runner` agent to triage: parse failure, identify which gate (label/handler/route) is the cause, suggest the smallest fix.

## Authoring a new persona

Copy `${CLAUDE_PLUGIN_ROOT}/templates/persona-journey.spec.ts.tmpl` to `tests/persona/<persona>.spec.ts`. Each spec narrates one critical path end-to-end. Specs are written *before* the page works — failing spec is the proof of work.
