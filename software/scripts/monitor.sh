#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
require_toolchain
port="${1:-}"
if [[ -z "$port" ]]; then
  arduino board list --json > "$PROJECT_ROOT/.tools/ports.json"
  port="$(python3 "$PROJECT_ROOT/scripts/detect_port.py" < "$PROJECT_ROOT/.tools/ports.json")"
fi
arduino monitor --port "$port" --config baudrate=115200
