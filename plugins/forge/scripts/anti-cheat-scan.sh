#!/usr/bin/env bash
# Thin wrapper. Delegates to python scanner for proper YAML allowlist support.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/anti_cheat_scan.py" "${1:-fast}"
