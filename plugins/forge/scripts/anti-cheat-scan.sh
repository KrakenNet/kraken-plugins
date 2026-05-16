#!/usr/bin/env bash
# Thin wrapper. Delegates to python scanner for proper allowlist support.
# Usage: anti-cheat-scan.sh [fast|full|stubs-state] [--strict]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-fast}"
shift || true
exec python3 "${SCRIPT_DIR}/anti_cheat_scan.py" "${MODE}" "$@"
