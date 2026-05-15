---
description: Show forge state — phase reached, prd.json task progress, last gate fired, blockers.
allowed-tools: [Bash, Read]
---

# /forge:status

## Run

```bash
if [ ! -d .forge ]; then
  echo "no .forge/ — nothing in flight"
  exit 0
fi

echo "=== Phase artifacts ==="
for f in interview/pm.md interview/design.md research/context.md research/pattern.md prd.md shared.md prd.json; do
  if [ -f ".forge/$f" ]; then
    printf "  [x] %-30s %s\n" "$f" "$(stat -c %y ".forge/$f" 2>/dev/null | cut -d. -f1)"
  else
    printf "  [ ] %s\n" "$f"
  fi
done

if [ -f .forge/prd.json ]; then
  echo ""
  echo "=== Tasks ==="
  jq -r '.tasks[] | "  [\(if .passes then "x" else " " end)] \(.id) — \(.title)"' .forge/prd.json 2>/dev/null
  echo ""
  total=$(jq '.tasks | length' .forge/prd.json)
  passed=$(jq '[.tasks[] | select(.passes)] | length' .forge/prd.json)
  echo "Progress: $passed / $total"
fi

if [ -d .forge/reviews ]; then
  echo ""
  echo "=== Inter-stage reviews ==="
  ls -1 .forge/reviews/ 2>/dev/null | sed 's/^/  /'
fi

if [ -f .forge/blockers.md ]; then
  echo ""
  echo "=== BLOCKERS ==="
  cat .forge/blockers.md
fi

echo ""
echo "=== Graph ==="
if [ -f .forge/memory/graph.db ]; then
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" status 2>/dev/null | sed 's/^/  /'
else
  echo "  not indexed yet (run /forge:graph rebuild)"
fi

echo ""
echo "=== Performance pack ==="
if [ -f .forge/lessons.md ]; then
  n=$(grep -c '^- ' .forge/lessons.md 2>/dev/null || echo 0)
  echo "  lessons: $n bullets"
else
  echo "  lessons: none yet"
fi
if [ -f .forge/recipes.jsonl ]; then
  n=$(wc -l < .forge/recipes.jsonl)
  echo "  recipes: $n entries"
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recipes.py" stats 2>/dev/null | sed 's/^/    /'
else
  echo "  recipes: none yet"
fi
```
