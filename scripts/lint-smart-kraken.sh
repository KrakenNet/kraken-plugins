#!/usr/bin/env bash
# Enforce that every smart-kraken SKILL.md copy is byte-identical to the canonical one in fathom.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT/plugins/fathom/skills/smart-kraken/SKILL.md"
[ -f "$CANONICAL" ] || { echo "missing canonical: $CANONICAL"; exit 1; }
CANON_HASH=$(sha256sum "$CANONICAL" | awk '{print $1}')
EXIT=0
for plugin in fathom nautilus harbor; do
  COPY="$ROOT/plugins/$plugin/skills/smart-kraken/SKILL.md"
  if [ ! -f "$COPY" ]; then
    # Only enforce for plugins that ship smart-kraken; skip if missing.
    continue
  fi
  H=$(sha256sum "$COPY" | awk '{print $1}')
  if [ "$H" != "$CANON_HASH" ]; then
    echo "DIFF: $COPY (sha=$H) != canonical (sha=$CANON_HASH)"
    EXIT=1
  fi
done
[ $EXIT -eq 0 ] && echo "OK: all smart-kraken copies match canonical"
exit $EXIT
