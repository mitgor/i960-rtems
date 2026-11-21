#!/usr/bin/env bash
# Rebuild the two-phase volatile copy stub; never opens PCI or writes flash.
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "usage: $0 TOOLCHAIN_BIN OUT_DIR" >&2
  exit 2
fi
tools_bin=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
"$tools_bin/i960-elf-as" -AJX "$here/stock_ram_even_copy.S" \
  -o "$out/stock_ram_even_copy.o"
"$tools_bin/i960-elf-ld" -T "$here/stock_ram_even_copy.ld" \
  -o "$out/stock_ram_even_copy.elf" "$out/stock_ram_even_copy.o"
"$tools_bin/i960-elf-objcopy" -O binary \
  "$out/stock_ram_even_copy.elf" "$out/stock_ram_even_copy.bin"
"$tools_bin/i960-elf-nm" -n "$out/stock_ram_even_copy.elf" \
  > "$out/stock_ram_even_copy.symbols"
python3 - "$out/stock_ram_even_copy.bin" "$out/stock_ram_even_copy.symbols" <<'PY'
import hashlib
from pathlib import Path
import sys

image = Path(sys.argv[1]).read_bytes()
symbols = Path(sys.argv[2]).read_text()
expected = 'b53589120254d24f1a4e69b1cbe1acb7813f2e8acc031a952221c9f6e521eedd'
if (len(image) != 296 or hashlib.sha256(image).hexdigest() != expected or
        'c000fe40 T stock_ram_even_copy' not in symbols):
    raise ValueError('volatile copy stub identity changed')
print(expected, sys.argv[1])
PY
