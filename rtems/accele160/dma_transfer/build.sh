#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 ]]; then echo "usage: $0 RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR" >&2; exit 2; fi
rtems_build=$(cd "$1" && pwd)
tools_bin=$(cd "$2" && pwd)
src=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$3"
out=$(cd "$3" && pwd)
for item in start timer_isr cache; do
  "$tools_bin/i960-coff-gcc" -mrp -c "$src/$item.S" -o "$out/$item.o"
done
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -D__rtems__ -DUSE_INLINES -I"$rtems_build/include" \
  -I"$(dirname "$rtems_build")/newlib-1.11.0/newlib/libc/include" \
  -c "$src/app.c" -o "$out/app.o"
"$tools_bin/i960-elf-ld" -T "$src/link.ld" -Map "$out/kernel.map" \
  -o "$out/kernel.elf" "$out/start.o" "$out/app.o" \
  "$out/timer_isr.o" "$out/cache.o" "$rtems_build/context.o" \
  "$rtems_build/libc.o" "$rtems_build/librtems-bounded.a"
"$tools_bin/i960-elf-objcopy" -O binary "$out/kernel.elf" "$out/kernel.bin"
"$tools_bin/i960-elf-nm" -n "$out/kernel.elf" > "$out/kernel.symbols"
python3 - "$out" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); image=(p/'kernel.bin').read_bytes()
assert len(image)==19*4096,len(image)
(p/'image.bin').write_bytes(image[:15*4096]+b'\xa5'*(4*4096))
PY
sha256sum "$out/kernel.bin" "$out/image.bin"
