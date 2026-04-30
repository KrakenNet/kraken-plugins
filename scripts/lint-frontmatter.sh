#!/usr/bin/env bash
# Lint that every command/agent/skill markdown file has valid YAML frontmatter
# with required keys.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXIT=0
for f in $(find "$ROOT/plugins" -path '*/commands/*.md' -o -path '*/agents/*.md' -o -path '*/skills/*/SKILL.md'); do
  HEAD=$(head -1 "$f")
  if [ "$HEAD" != "---" ]; then
    echo "FAIL: missing frontmatter: $f"
    EXIT=1
    continue
  fi
  if ! grep -qE '^description:' "$f"; then
    echo "FAIL: missing description: $f"
    EXIT=1
  fi
  if [[ "$f" == */SKILL.md ]] && ! grep -qE '^name:' "$f"; then
    echo "FAIL: skill missing name: $f"
    EXIT=1
  fi
done
[ $EXIT -eq 0 ] && echo "OK: frontmatter valid across plugins"
exit $EXIT
