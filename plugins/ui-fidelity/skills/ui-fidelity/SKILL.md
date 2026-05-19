---
name: ui-fidelity
description: Use when auditing a React/Vite UI for dead buttons, orphan routes, flow-continuity breaks, intent-contract violations, contrast bugs, persona-journey gaps, or LLM-grade UX issues. Loaded by ui-fidelity:* commands.
---

# ui-fidelity skill

This skill briefs an agent on the 8-gate audit harness. Read top-to-bottom before running any gate.

## Why this exists

tsc + eslint + vite-build green does not mean the UI works. Common failure modes the test suites miss:

- Button rendered with `onClick={undefined}` or `onClick={() => {}}` → looks fine, does nothing
- Route registered in `App.tsx`, no `<Link>` to it anywhere → unreachable
- Toast component absolutely-positioned outside viewport → user never sees feedback
- Input + button on landing page, button handler ignores input → user types, click does wrong thing
- Page renders, primary CTA opens chat when label says "Build" → label/behavior mismatch
- Persona path "type prompt → Build → designer with prompt prefilled" silently broken across two PRs

The harness catches each as a separate gate so a failure points at the actual root cause.

## Gate-by-gate contract

### 1. console-error

Playwright loads each route, listens on `console.error` + `pageerror`. Any event fails the gate. Whitelist via `.ui-fidelity/console-allow.json` (per-route regex array).

### 2. dead-button

For each route, query `button, a[role=button], [data-action]`. For each element:

- If `disabled` → skip
- Click it, capture: URL change, network requests (count + URLs), DOM mutations on `document.body`, toast events
- If none of those changed → dead button → fail with selector + text

### 3. orphan-route

Parse routes from `src/App.tsx` (or `src/routes/` filesystem if present). For each non-detail route (`/foo`, not `/foo/:id`), grep for `<Link to="/foo"` or `navigate('/foo')` *outside* the route's own file tree. None found → orphan → fail.

Allow-list for entry routes (`/`, `/login`, `/onboarding/*`) via `.ui-fidelity/orphan-allow.json`.

### 4. contrast / axe

`@axe-core/playwright` over each route. WCAG AA violations fail. Plus custom checks:

- Toast: compute `getBoundingClientRect()` on any element with `[role=status]` or `[role=alert]`; `bottom > window.innerHeight` → fail
- Spot-check `data-cta`, `data-action`, `h1..h6` elements: computed `color` vs `background-color` contrast ratio < 4.5 → fail

### 5. flow-continuity (static)

For each route file, AST-walk: collect `<input>` / `<textarea>` / `<select>` JSX nodes and their `value`/`onChange` bindings; collect primary CTA (element with `data-cta="primary"` or first `<button type="submit">` or first `data-action`). The CTA's `onClick`/`onSubmit` handler must reference at least one of the collected input bindings. None referenced → orphan input → fail.

### 6. intent-contract

For each touched route, require `INTENT.md` sibling file. Parse:

```
route: <string>
persona: <string>
primary-goal: <string>
primary-cta:
  label: <string>
  target: <string>   # navigate(...), open-drawer(...), submit(...), etc
secondary-ctas: [...]
prohibited: [...]
```

Checks:

- Missing file when route was edited → fail (suggest `/ui-fidelity:intent <route>`)
- Primary CTA's actual handler does not match declared `target` → fail (grep primary CTA in source, compare destination)
- Any `prohibited` component imported in route file → fail

### 7. persona-journey

Playwright spec per persona under `tests/persona/<persona>.spec.ts`. Spec narrates the user flow. Harness runs all + collects results. Missing spec when an `INTENT.md` declares that persona → fail.

Template at `templates/persona-journey.spec.ts.tmpl`.

### 8. llm-ux-critic

For each route:

1. Playwright loads, screenshots at 1440x900
2. Capture DOM snapshot (text + roles), strip class attrs
3. Read sibling `INTENT.md`
4. POST to `${UI_FIDELITY_LLM_BASE:-http://localhost:41001}/v1/chat/completions` with:

```
system: You are an adversarial UX critic. Given a persona, primary goal, and a
rendered page, list (a) dead-ends, (b) redundant or off-persona CTAs, (c)
label/behavior mismatches, (d) missing primary path. Be specific. Cite element
text. Output JSON: { findings: [{severity, kind, element, why}] }.

user: { persona, goal, prohibited, screenshot_b64, dom_text }
```

5. Findings with `severity >= warn` fail the gate (configurable).

Costs are bounded by running last after cheaper gates pass.

## How to run

`/ui-fidelity:audit` dispatches the orchestrator agent. The orchestrator:

1. Detects project shape (React/Vite, Playwright, package manager)
2. Determines target pages (default: `git diff --name-only main...HEAD | grep src/routes/`)
3. Spawns gate agents 1-7 in parallel (each is read-only)
4. If 1-7 pass, runs gate 8 (LLM critic, slow)
5. Writes `.ui-fidelity/report.json` + `.md`
6. Exits 1 on any failure

## Hooks (optional)

Plugin can install a `PostToolUse` hook (Edit/Write) that, when a file under `src/routes/**` is changed, schedules a lightweight version of gates 5, 6 to run before the next user prompt. Opt-in via `.ui-fidelity/hooks.enabled`.

## Project bootstrap

First run on a new repo creates `.ui-fidelity/` with:

- `config.json` — gate enable/disable flags, allow-lists
- `console-allow.json`, `orphan-allow.json` — empty allowlists
- `templates/` — copied from plugin
- `INTENT.md` scaffolds in every touched route file (via `/ui-fidelity:intent --all`)

Never overwrites existing user-authored `INTENT.md`.
