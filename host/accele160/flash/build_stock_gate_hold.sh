#!/usr/bin/env bash
# Build only; never opens PCI. An optional third argument overrides the hold
# poll count; the launcher then refuses the result until its pin is updated.
set -euo pipefail
if [[ $# != 2 && $# != 3 ]]; then
  echo "usage: $0 TOOLCHAIN_BIN OUT_DIR [HOLD_POLLS]" >&2
  exit 2
fi
tools_bin=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
"$tools_bin/i960-elf-as" -AJX ${3:+--defsym HOLD_POLLS=$3} \
  "$here/stock_gate_hold.S" -o "$out/gate-hold.o"
"$tools_bin/i960-elf-ld" -Ttext 0xc000f900 \
  -o "$out/gate-hold.elf" "$out/gate-hold.o"
"$tools_bin/i960-elf-objcopy" -O binary \
  "$out/gate-hold.elf" "$out/gate-hold.bin"
if [[ $# == 2 ]]; then
  cmp "$out/gate-hold.bin" "$here/stock_gate_hold.bin"
fi
shasum -a 256 "$out/gate-hold.bin" 2>/dev/null || sha256sum "$out/gate-hold.bin"
