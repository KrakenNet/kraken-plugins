---
description: View, prune, or query forge lessons (.forge/lessons.md). Reflexion-style log of generalizable insights from past task runs.
argument-hint: [list | prune | context --tags X | add <tags> <body>]
allowed-tools: [Bash]
---

# /forge:lessons

## Usage

```bash
# default: list all, newest first
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py" list

# filter by tag
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py" list --tag anti-cheat

# context bundle for agent injection (caps tokens)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py" context --tags "ralph,auth" --max-tokens 800

# prune to newest 50
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py" prune --keep 50

# manual add
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lessons.py" add "tag1,tag2" "lesson body"
```

Parse `$ARGUMENTS` and dispatch to matching subcommand. Default to `list`.
