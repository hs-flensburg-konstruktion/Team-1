#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
port=""
if [[ $# -gt 0 ]]; then
  [[ $# -eq 2 && "$1" == --port ]] || { echo 'Aufruf: ./scripts/upload.sh [--port /dev/cu.usbmodem…]' >&2; exit 1; }
  port="$2"
fi
"$PROJECT_ROOT/scripts/build.sh"
if [[ -z "$port" ]]; then
  arduino board list --json > "$PROJECT_ROOT/build/ports.json"
  port="$(python3 "$PROJECT_ROOT/scripts/detect_port.py" < "$PROJECT_ROOT/build/ports.json")"
fi
[[ -c "$port" ]] || { echo "Kein serieller Geräteport: $port" >&2; exit 1; }
echo "Upload auf $port"
arduino upload --fqbn "$FQBN" --port "$port" --input-dir "$PROJECT_ROOT/build/artifacts" "$SKETCH"
