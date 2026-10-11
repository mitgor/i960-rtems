#!/bin/sh
# Run in a deployed project tree on the Linux build host. No card access.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$here/../.." && pwd)
out=$1
cross=${CROSS:-/home/mit/i960/tools/bin/i960-coff-}
mkdir -p "$out"
"${cross}gcc" -mrp -O2 -ffreestanding -fno-builtin -I"$root/loader/runtime" -c "$here/inventory.c" -o "$out/inventory.o"
"${cross}gcc" -mrp -c "$root/loader/runtime/buffer_start.s" -o "$out/start.o"
"${cross}ld" -T "$root/loader/runtime/buffer.ld" -Map="$out/inventory.map" "$out/start.o" "$out/inventory.o" -o "$out/inventory.elf"
"${cross}objcopy" -O binary "$out/inventory.elf" "$out/inventory.bin"
"${cross}objdump" -dr "$out/inventory.elf" > "$out/inventory.dis"
python3 "$root/host/loadrun/build.py" --out "$out/module"
make -C "/lib/modules/$(uname -r)/build" M="$out/module" modules
