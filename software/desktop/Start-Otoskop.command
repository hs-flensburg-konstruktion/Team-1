#!/bin/bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Richte die lokale Python-Umgebung ein …'
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6.QtWidgets, esptool, serial' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r desktop/requirements.txt
fi
exec .venv/bin/python desktop/main.py "$@"
