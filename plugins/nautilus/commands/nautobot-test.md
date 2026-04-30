---
description: Connection test for the Nautilus Nautobot adapter (P0 issue)
argument-hint: [--url <url>] [--token <token>]
allowed-tools: [Bash, Read]
---

# Nautobot Connection Test

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Run

```bash
uv run python -c "
from nautilus_adapter_nautobot import Adapter
a = Adapter(url='${NAUTOBOT_URL}', token='${NAUTOBOT_TOKEN}')
print(a.health())
print(list(a.query({'data_type':'device','limit':3})))
"
```

## Report

Health + 3 sample devices + auth-status + GraphQL/REST mode used.
