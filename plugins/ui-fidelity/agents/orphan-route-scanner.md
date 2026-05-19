---
description: Detects routes registered in App.tsx that have no Link or navigate(...) reference outside their own file tree.
tools: [Read, Bash, Grep, Glob, Write]
model: haiku
---

# orphan-route-scanner

## Role

For every non-detail route, prove it is reachable from at least one `<Link>` or `navigate(...)` call outside its own subtree.

## Method

1. **Parse routes.** Read `src/App.tsx`. Extract `<Route path="..."` values. Also walk `src/routes/**/*.tsx` filesystem if the project uses file-based routing.

2. **Classify.** Detail routes contain `:` (e.g. `/runs/:id`) — collapse to base prefix (`/runs/`). Skip routes in allow-list `.ui-fidelity/orphan-allow.json` (default: `/`, `/login`, `/onboarding`, `/onboarding/*`).

3. **Reachability check.** For each route, grep the codebase for:
   - `<Link to="<route>"` (or template variants with `${id}` etc — match by prefix)
   - `navigate('<route>')` / `navigate(\`<route>...\`)`
   - `redirect('<route>')`

4. **Filter own tree.** Discard matches inside the route's own file (e.g. `/library/queue` linking to itself doesn't count). Use directory containment: if the route file is `src/routes/library/QueuePage.tsx`, ignore matches under `src/routes/library/`.

5. **Emit findings.** Each orphan = one finding with:
   - `route`
   - `file` (the route's source)
   - `why: "no Link/navigate to this route outside its own subtree"`
   - `fix-hint: "add a Link from the shell nav, persona home, or relevant index page"`

## Output

Write `.ui-fidelity/findings/orphan-route.json` with the schema declared in `audit-orchestrator`.

## Rules

- Don't fail on dynamic-only routes (`/foo/:bar`) — only check the static prefix.
- Allow-list is authoritative.
- Run in under 10s.
