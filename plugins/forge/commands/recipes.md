---
description: Failure recipe DB (.forge/recipes.jsonl). Lookup past blocker resolutions, list, stats, manual add.
argument-hint: [lookup <query> | list | stats | add ...]
allowed-tools: [Bash]
---

# /forge:recipes

## Usage

```bash
# find recipes matching a failure symptom
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" lookup "playwright timeout selector" --max 3

# filter by category
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" lookup "..." --category adversarial-fail

# list recent
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" list --max 10

# counts by category
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" stats

# manual add (normally written by lessons-keeper)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" add \
  --category lint-fail \
  --symptom "eslint no-unused-vars on test imports" \
  --resolution "remove unused import; this lint rule fires on all unused" \
  --task auth-middleware \
  --files "src/auth/middleware.ts"
```

Parse `$ARGUMENTS` and dispatch. Default to `stats`.
