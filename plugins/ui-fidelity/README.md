# ui-fidelity

Multi-gate UI audit harness. Built because tsc + eslint + vite-build green ≠ working UI.

## Gates

| # | Gate | Catches |
|---|------|---------|
| 1 | console-error | Uncaught errors at page load |
| 2 | dead-button | `<button>` with no handler or with handler that has zero side effect |
| 3 | orphan-route | Route in `App.tsx` not linked from any `<Link>` outside its own subtree |
| 4 | contrast/axe | WCAG AA violations, white-on-white text, toast under viewport |
| 5 | flow-continuity | Input/textarea on surface whose primary CTA does not consume its value |
| 6 | intent-contract | Page touched without `INTENT.md`; primary CTA wires to wrong target; prohibited components mounted |
| 7 | persona-journey | Scripted user narrative fails (Playwright spec per persona) |
| 8 | llm-ux-critic | LLM reads screenshot + DOM + INTENT.md, flags label/behavior mismatches and dead-ends |

## Commands

- `/ui-fidelity:audit [path...]` — full audit, all gates, on changed/given pages
- `/ui-fidelity:intent <route>` — scaffold or edit `INTENT.md` next to a route
- `/ui-fidelity:persona <persona>` — run persona-journey suite
- `/ui-fidelity:critic <route>` — LLM-as-critic pass only (cheap, fast)

## INTENT.md contract

Every interactive route has a sibling `INTENT.md`:

```
route: /developer
persona: developer
primary-goal: ship a working graph in under 30 seconds
primary-cta:
  label: Build
  target: navigate(/designer/:newId) with prompt forwarded
secondary-ctas:
  - recent graphs (max 3)
  - empty-state: link to library only if user has zero graphs
prohibited:
  - marketplace browse on this surface (wrong persona target)
  - opening chat panel as primary action (chat lives in shell)
```

Audit reads this and asserts behavior matches.

## Project requirements

- React + Vite + Playwright + TypeScript (tested shape; other stacks pending)
- `pnpm` or `npm`
- `axe-core/playwright` installed (auto-installed if absent)
- `localhost:41001` OpenAI-compat LLM for `/critic` gate (configurable via `UI_FIDELITY_LLM_BASE`)

## Output

Single JSON report `.ui-fidelity/report.json` + readable Markdown summary `.ui-fidelity/report.md`. Exit code 1 if any gate fails.
