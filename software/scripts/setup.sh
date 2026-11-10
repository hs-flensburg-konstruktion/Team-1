#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
command -v python3 >/dev/null || { echo 'Python 3 wird benötigt.' >&2; exit 1; }
[[ "$(uname -s)" == Darwin ]] || { echo 'Dieses Setup ist für macOS vorgesehen.' >&2; exit 1; }
case "$(uname -m)" in arm64) cli_arch=ARM64 ;; x86_64) cli_arch=64bit ;; *) exit 1 ;; esac
mkdir -p "$PROJECT_ROOT/.tools/bin" "$PROJECT_ROOT/.tools/downloads"
if [[ ! -x "$CLI" ]] || ! "$CLI" version | grep -Fq "Version: $ARDUINO_CLI_VERSION "; then
  archive="arduino-cli_${ARDUINO_CLI_VERSION}_macOS_${cli_arch}.tar.gz"
  release="https://github.com/arduino/arduino-cli/releases/download/v$ARDUINO_CLI_VERSION"
  curl -fL --retry 3 "$release/$archive" -o "$PROJECT_ROOT/.tools/downloads/$archive"
  curl -fL --retry 3 "$release/${ARDUINO_CLI_VERSION}-checksums.txt" -o "$PROJECT_ROOT/.tools/downloads/checksums.txt"
  (cd "$PROJECT_ROOT/.tools/downloads"; grep " $archive\$" checksums.txt | shasum -a 256 -c -)
  tar -xzf "$PROJECT_ROOT/.tools/downloads/$archive" -C "$PROJECT_ROOT/.tools/bin" arduino-cli
fi
configure_cli
arduino core list --json > "$PROJECT_ROOT/.tools/installed-cores.json"
if ! python3 - "$PROJECT_ROOT/.tools/installed-cores.json" "$ESP32_CORE_VERSION" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
sys.exit(0 if not d.get('warnings') and any(p['id'] == 'esp32:esp32' and p.get('installed_version') == sys.argv[2] for p in d.get('platforms', [])) else 1)
PY
then
  arduino core update-index
  arduino core install "esp32:esp32@$ESP32_CORE_VERSION"
fi
require_toolchain
"$PROJECT_ROOT/scripts/setup-ctags.sh"
arduino board details --fqbn "$FQBN" > "$PROJECT_ROOT/.tools/board-details.txt"
"$CLI" version
echo "Espressif $ESP32_CORE_VERSION bereit: $FQBN"
