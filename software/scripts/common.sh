#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_ROOT/config/versions.env"
CLI="$PROJECT_ROOT/.tools/bin/arduino-cli"
CLI_CONFIG="$PROJECT_ROOT/.tools/arduino-cli.yaml"
SKETCH="$PROJECT_ROOT/firmware/Otoskop"
FQBN="$BOARD_FQBN:$BOARD_OPTIONS"

configure_cli() {
  mkdir -p "$PROJECT_ROOT/.tools/cache" "$PROJECT_ROOT/.tools/sketchbook"
  python3 - "$PROJECT_ROOT" "$ESP32_INDEX_URL" <<'PY'
import json, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
# Existing Espressif toolchains are shared with Arduino IDE; project settings stay local.
data = os.environ.get('OTOSKOP_ARDUINO_DATA', str(pathlib.Path.home() / 'Library/Arduino15'))
config = {'board_manager': {'additional_urls': [sys.argv[2]]},
          'directories': {'data': data, 'downloads': str(root / '.tools/downloads'),
                          'user': str(root / '.tools/sketchbook')},
          'build_cache': {'path': str(root / '.tools/cache')},
          'updater': {'enable_notification': False}}
(root / '.tools/arduino-cli.yaml').write_text(json.dumps(config, indent=2) + '\n')
PY
}
arduino() { "$CLI" --config-file "$CLI_CONFIG" "$@"; }
require_toolchain() {
  if [[ ! -x "$CLI" ]]; then
    echo 'Arduino CLI fehlt. Zuerst ./scripts/setup.sh ausführen.' >&2; exit 1
  fi
  configure_cli
  if ! "$CLI" version | grep -Fq "Version: $ARDUINO_CLI_VERSION "; then
    echo 'CLI-Version weicht von config/versions.env ab. ./scripts/setup.sh ausführen.' >&2; exit 1
  fi
  arduino core list --json > "$PROJECT_ROOT/.tools/installed-cores.json"
  python3 - "$PROJECT_ROOT/.tools/installed-cores.json" "$ESP32_CORE_VERSION" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if d.get('warnings'):
    sys.exit('Arduino CLI konnte Pakete nicht fehlerfrei laden: ' + '; '.join(d['warnings']))
if not any(p['id'] == 'esp32:esp32' and p.get('installed_version') == sys.argv[2]
           for p in d.get('platforms', [])):
    sys.exit('Erwarteter Espressif-Core fehlt. ./scripts/setup.sh ausführen.')
PY
}
