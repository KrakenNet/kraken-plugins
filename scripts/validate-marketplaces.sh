#!/usr/bin/env bash
# Validate both marketplaces parse, agree on plugin set, and have valid sources.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for f in "$ROOT/.claude-plugin/marketplace.json" "$ROOT/.cursor-plugin/marketplace.json"; do
  python3 -c "import json; json.load(open('$f'))" || { echo "invalid JSON: $f"; exit 1; }
done
python3 - <<PY
import json, os, sys
root = "$ROOT"
a = json.load(open(f"{root}/.claude-plugin/marketplace.json"))
b = json.load(open(f"{root}/.cursor-plugin/marketplace.json"))
if a != b:
    print("FAIL: claude and cursor marketplaces diverge")
    sys.exit(1)
for p in a["plugins"]:
    src = os.path.join(root, p["source"])
    if not os.path.isdir(src):
        print(f"FAIL: missing plugin dir for {p['name']}: {src}")
        sys.exit(1)
    manifest = os.path.join(src, ".claude-plugin", "plugin.json")
    if not os.path.isfile(manifest):
        print(f"FAIL: missing manifest for {p['name']}: {manifest}")
        sys.exit(1)
print("OK: marketplaces valid, all plugin dirs and manifests present")
PY
