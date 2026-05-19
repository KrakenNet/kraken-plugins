---
description: Scaffold or edit INTENT.md for a route. Required before /ui-fidelity:audit will pass gate 6 on that route.
argument-hint: <route-path> | --all
allowed-tools: [Read, Write, Edit, Glob, Grep, AskUserQuestion]
---

# /ui-fidelity:intent

Author `INTENT.md` next to a route file.

## Args

- `<route-path>` → scaffold for one file (e.g. `src/routes/developer/DeveloperHome.tsx`)
- `--all` → walk every route file under `src/routes/**` and offer to scaffold missing ones

## Process

For each target:

1. Resolve sibling `INTENT.md` path (same dir as route file, named `INTENT.md` if one route, or `<RouteName>.INTENT.md` if multiple)
2. If exists, open for edit instead of overwrite
3. Read template from `${CLAUDE_PLUGIN_ROOT}/templates/INTENT.md.tmpl`
4. Use AskUserQuestion to fill required fields:
   - persona (one of: developer | reviewer | auditor | admin | plugin-dev | tenant-admin | guest)
   - primary-goal (one sentence, time-bounded)
   - primary-cta label + target (free text, target must be `navigate(/...)`, `open-drawer(...)`, `submit(...)`, or `external(...)`)
   - prohibited components (optional, comma-separated)
5. Write file
6. Print: `wrote <path>. Run /ui-fidelity:audit --routes <route> to verify.`

## Why this matters

Without INTENT.md the auditor cannot detect label/behavior mismatches or off-persona CTAs. Those are the bugs lint+tsc miss.
