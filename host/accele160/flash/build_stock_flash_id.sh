#!/usr/bin/env bash
# Build only; never opens PCI or issues a flash command.
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "usage: $0 TOOLCHAIN_BIN OUT_DIR" >&2
  exit 2
fi
tools_bin=$(cd "$1" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -c "$here/stock_flash_id.c" -o "$out/stock_flash_id.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -c "$root/rtems/accele160/ram_loader/flash_identify_payload.c" \
  -o "$out/flash_identify_payload.o"
"$tools_bin/i960-elf-as" -AJX "$here/stock_flash_id_entry.S" \
  -o "$out/stock_flash_id_entry.o"
"$tools_bin/i960-elf-ld" -T "$here/stock_flash_id.ld" \
  -Map "$out/flash-id.map" -o "$out/flash-id.elf" \
  "$out/stock_flash_id_entry.o" "$out/stock_flash_id.o" \
  "$out/flash_identify_payload.o"
"$tools_bin/i960-elf-objcopy" -O binary \
  "$out/flash-id.elf" "$out/flash-id.bin"
"$tools_bin/i960-elf-nm" -n "$out/flash-id.elf" > "$out/flash-id.symbols"
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib
import sys

out = Path(sys.argv[1])
image = (out / "flash-id.bin").read_bytes()
symbols = (out / "flash-id.symbols").read_text()
if (len(image) != 356 or
        image[:8] != bytes.fromhex("0030808c00f800c0") or
        image[0x14:0x18] != bytes.fromhex("00500484") or
        "c000f900 T stock_flash_id_entry" not in symbols):
    raise ValueError("stock RAM flash-ID entry, fallback, or size changed")
print(hashlib.sha256(image).hexdigest(), out / "flash-id.bin")
PY
