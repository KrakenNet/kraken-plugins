#!/usr/bin/env bash
# UserPromptSubmit hook. Surfaces forge state if .forge/ exists.
# Output appended as additional context for the conversation.

set -euo pipefail

[ -d .forge ] || exit 0

# Don't spam every prompt — only if prd.json exists (Phase 2 entered)
[ -f .forge/prd.json ] || exit 0

total=$(jq '.tasks | length // 0' .forge/prd.json 2>/dev/null || echo 0)
passed=$(jq '[.tasks[] | select(.passes)] | length // 0' .forge/prd.json 2>/dev/null || echo 0)

[ "$total" = "0" ] && exit 0

echo "Forge state: $passed/$total tasks pass. Run /forge:status for details, /forge:resume to continue Ralph Loop."

# Surface blockers if any
[ -f .forge/blockers.md ] && echo "BLOCKERS exist in .forge/blockers.md — resolve before resuming."

exit 0
