#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
require_toolchain
[[ -x "$PROJECT_ROOT/.tools/native-ctags/ctags" ]] || { echo 'Natives ctags fehlt. ./scripts/setup.sh ausführen.' >&2; exit 1; }
mkdir -p "$PROJECT_ROOT/build/artifacts" "$PROJECT_ROOT/build/compiler"
arduino compile --fqbn "$FQBN" --warnings all --jobs 4 \
  --build-property "runtime.tools.ctags.path=$PROJECT_ROOT/.tools/native-ctags" \
  --build-property "tools.ctags.path=$PROJECT_ROOT/.tools/native-ctags" \
  --build-path "$PROJECT_ROOT/build/compiler" --output-dir "$PROJECT_ROOT/build/artifacts" \
  "$SKETCH" 2>&1 | tee "$PROJECT_ROOT/build/compile.log"
echo 'Build erfolgreich: build/artifacts/'
