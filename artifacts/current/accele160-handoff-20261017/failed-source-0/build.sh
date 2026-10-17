#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then echo "usage: $0 TOOLCHAIN_BIN OUT_DIR" >&2; exit 2; fi
tools_bin=$(cd "$1" && pwd)
src=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
"$tools_bin/i960-coff-gcc" -mrp -c "$src/start.S" -o "$out/start.o"
"$tools_bin/i960-coff-gcc" -mrp -c "$src/timer_isr.S" -o "$out/timer_isr.o"
"$tools_bin/i960-coff-gcc" -mrp -c "$src/cache.S" -o "$out/cache.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -ffreestanding -fno-builtin \
  -c "$src/app.c" -o "$out/app.o"
"$tools_bin/i960-elf-ld" -T "$src/link.ld" -Map "$out/image.map" \
  -o "$out/image.elf" "$out/start.o" "$out/timer_isr.o" \
  "$out/cache.o" "$out/app.o"
"$tools_bin/i960-elf-objcopy" -O binary "$out/image.elf" "$out/image-raw.bin"
"$tools_bin/i960-elf-nm" -n "$out/image.elf" > "$out/image.symbols"
python3 - "$out" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);raw=(p/'image-raw.bin').read_bytes()
assert len(raw)==3*4096,len(raw)
# Full second page is dedicated ISR storage; the third is entry stack.
(p/'image.bin').write_bytes(raw[:4096]+b'\xa5'*(2*4096))
PY
sha256sum "$out/image.bin"
