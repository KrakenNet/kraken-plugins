---
description: List and manage KB gap files — view known inaccuracies, resolve gaps
argument-hint: [path] [--list] [--resolve N]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep]
---

# KB Gaps

Manage gap files that document known discrepancies between KB articles and the codebase.

## Parse Arguments

From `$ARGUMENTS`:
- **No args or --list**: list all gap files across the KB
- **path**: article path (e.g., `agents/overview.md`) — show gaps for that article
- **path --resolve N**: resolve gap number N in the specified article's gap file

## Route by Action

### List (no args or --list)

Find all gap files:
```bash
find docs/ -name "*-gaps.md" -not -path "*/superpowers/*" | sort
```

For each gap file:
1. Count the number of `## Gap` sections
2. Read the first line of each gap section title

Display as a table:

```
| Article | Gap File | Gaps |
|---------|----------|------|
| agents/overview.md | agents/overview-gaps.md | 3 |
| governors/runtime.md | governors/runtime-gaps.md | 2 |

Total: N gap files, M total gaps
```

### Show (path provided, no --resolve)

1. Derive the gap file path: if the article is `docs/<domain>/<name>.md`, the gap file is `docs/<domain>/<name>-gaps.md`
2. Check if it exists:
   ```bash
   test -f docs/<domain>/<name>-gaps.md && echo "EXISTS" || echo "NONE"
   ```
3. If NONE: report "No gaps documented for <path>"
4. If EXISTS: read and display the full gap file contents

### Resolve (path + --resolve N)

1. Derive and read the gap file
2. Find `## Gap N:` section
3. If not found: error "Gap N not found in <gap-file>"
4. Remove the entire section (from `## Gap N:` to the next `## Gap` or end of file)
5. Renumber remaining gaps sequentially (Gap 1, Gap 2, ...)
6. If no gaps remain: delete the gap file entirely
7. Report what was resolved

## No Agent Needed

This command operates directly — no subagent delegation. Gap file operations are simple read/edit/delete.
