#!/usr/bin/env bash
# Thin wrapper. Delegates to python scanner.
# Usage: architecture-scan.sh [fast|full|baseline|state] [--strict]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-fast}"
shift || true
exec python3 "${SCRIPT_DIR}/architecture_scan.py" "${MODE}" "$@"
