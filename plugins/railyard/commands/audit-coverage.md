---
description: Audit which Railyard API endpoints are covered by plugin commands; flag gaps
argument-hint: []
allowed-tools: [Bash, Read]
---

# Railyard API Coverage Audit

Compares the live Railyard router (via OpenAPI/swagger if available, else parses the source) against the commands in this plugin and lists gaps.

## Steps

1. Try to fetch `${RAILYARD_URL}/api/v1/docs/doc.json` (Swagger). If 200, parse `paths`.
2. Otherwise, suggest running locally against `railyard/internal/api/router.go`:

```bash
grep -E "^// Mount[A-Za-z]+ mounts" /home/sean/leagues/railyard/railyard/internal/api/router.go | sed -E 's/^.*mounts the [^ ]+ handler at //; s/\.//' | sort -u > /tmp/api-paths.txt
```

3. Build the set of covered endpoints by reading every command file in `${CLAUDE_PLUGIN_ROOT}/../railyard/commands/` and extracting `/api/v1/` matches.

4. Diff: report endpoints in router not in any command file.

## Report

Markdown table: endpoint | covered? | command(s) | suggested action.
