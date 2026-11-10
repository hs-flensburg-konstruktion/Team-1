#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
target="$PROJECT_ROOT/.tools/native-ctags"
[[ -x "$target/ctags" ]] && exit 0
command -v clang >/dev/null || { echo 'Apple Command Line Tools fehlen: xcode-select --install' >&2; exit 1; }
archive="$PROJECT_ROOT/.tools/downloads/ctags-$CTAGS_VERSION-source.tar.gz"
mkdir -p "$PROJECT_ROOT/.tools/downloads" "$PROJECT_ROOT/.tools/ctags-source" "$target"
if [[ ! -f "$archive" ]]; then
  curl -fL --retry 3 "https://github.com/arduino/ctags/archive/refs/tags/$CTAGS_VERSION.tar.gz" -o "$archive"
fi
printf '%s  %s\n' "$CTAGS_SOURCE_SHA256" "$archive" | shasum -a 256 -c -
tar -xzf "$archive" -C "$PROJECT_ROOT/.tools/ctags-source" --strip-components=1
# Arduino's 2017 source defines a reserved macro which conflicts with modern
# macOS SDK headers. Rename just this internal macro and its uses.
python3 - "$PROJECT_ROOT/.tools/ctags-source" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
for pattern in ('*.c', '*.h'):
    for path in root.glob(pattern):
        text = path.read_bytes()
        path.write_bytes(text.replace(b'__unused__', b'CTAGS_UNUSED'))
PY
(
  cd "$PROJECT_ROOT/.tools/ctags-source"
  ./configure CC=clang > ../ctags-configure.log 2>&1
  make clean > ../ctags-make.log 2>&1
  make -j4 ctags >> ../ctags-make.log 2>&1
  cp ctags "$target/ctags"
)
"$target/ctags" --version
