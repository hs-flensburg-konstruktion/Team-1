#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$root/build/tests"
clang++ -std=c++11 -Wall -Wextra -Werror -fsanitize=undefined "$root/tests/charge_status_test.cpp" -o "$root/build/tests/charge_status_test"
"$root/build/tests/charge_status_test"
clang++ -std=c++11 -Wall -Wextra -Werror -fsanitize=undefined "$root/tests/offline_control_test.cpp" -o "$root/build/tests/offline_control_test"
"$root/build/tests/offline_control_test"
clang++ -std=c++11 -Wall -Wextra -Werror "$root/tests/photo_names_test.cpp" -o "$root/build/tests/photo_names_test"
"$root/build/tests/photo_names_test"
clang++ -std=c++11 -Wall -Wextra -Werror -fsanitize=undefined "$root/tests/jpeg_dimensions_test.cpp" -o "$root/build/tests/jpeg_dimensions_test"
"$root/build/tests/jpeg_dimensions_test"
python3 "$root/tests/test_detect_port.py"
for script in "$root"/scripts/*.sh; do bash -n "$script"; done
echo 'JPEG-Auflösung, Foto-Dateinamen, Zählergrenzen, Portauswahl und Shell-Syntax: OK'
