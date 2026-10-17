#!/usr/bin/env bash
# Rebuild the reviewed 16-page RAM lease image with the pinned i960 tools.
set -euo pipefail
if [[ $# != 3 ]]; then
  echo "usage: $0 RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR" >&2
  exit 2
fi
rtems_build=$(cd "$1" && pwd)
tools_bin=$(cd "$2" && pwd)
out_dir=$3
src=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out_dir"
out_dir=$(cd "$out_dir" && pwd)
"$tools_bin/i960-coff-gcc" -mrp -c "$src/start.S" -o "$out_dir/start.o"
"$tools_bin/i960-coff-gcc" -mrp -c "$src/cache.S" -o "$out_dir/cache.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -D__rtems__ -DUSE_INLINES -I"$rtems_build/include" \
  -I"$(dirname "$rtems_build")/newlib-1.11.0/newlib/libc/include" \
  -c "$src/app.c" -o "$out_dir/app.o"
"$tools_bin/i960-elf-ld" -T "$src/link.ld" -Map "$out_dir/kernel.map" \
  -o "$out_dir/kernel.elf" "$out_dir/start.o" "$out_dir/app.o" \
  "$out_dir/cache.o" "$rtems_build/context.o" "$rtems_build/libc.o" \
  "$rtems_build/librtems-bounded.a"
"$tools_bin/i960-elf-objcopy" -O binary "$out_dir/kernel.elf" "$out_dir/kernel.bin"
"$tools_bin/i960-elf-nm" -n "$out_dir/kernel.elf" > "$out_dir/kernel.symbols"
python3 - "$out_dir" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
kernel=(p/'kernel.bin').read_bytes()
assert len(kernel)==65536, len(kernel)
(p/'image.bin').write_bytes(kernel[:15*4096]+b'\xa5'*4096)
PY
sha256sum "$out_dir/kernel.bin" "$out_dir/image.bin"
