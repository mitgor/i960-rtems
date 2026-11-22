#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "usage: $0 TOOLCHAIN_BIN OUT_DIR" >&2
  exit 2
fi
tools_bin=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
"$tools_bin/i960-elf-as" -AJX "$here/id_probe.S" -o "$out/id-probe.o"
"$tools_bin/i960-elf-ld" -Ttext 0xc0710000 -o "$out/id-probe.elf" "$out/id-probe.o"
"$tools_bin/i960-elf-objcopy" -O binary "$out/id-probe.elf" "$out/id-probe.bin"
"$tools_bin/i960-elf-objdump" -dr "$out/id-probe.elf" > "$out/id-probe.dis"
sha256sum "$out/id-probe.bin"
