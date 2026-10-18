#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 ]]; then echo "usage: $0 RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR" >&2; exit 2; fi
rtems_build=$(cd "$1" && pwd)
tools_bin=$(cd "$2" && pwd)
src=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$src/../../.." && pwd)
python3 "$repo/card_profiles/check.py" --card-profile "${CARD_PROFILE:-accele160}" --workflow rtems_accele160 >/dev/null
mkdir -p "$3"
out=$(cd "$3" && pwd)
"$tools_bin/i960-coff-gcc" -mrp -DACCELE_TERMINAL="${ACCELE_TERMINAL:-0}" -c "$src/../fault/terminal.S" -o "$out/terminal.o"
for item in start timer_isr cache; do
  "$tools_bin/i960-coff-gcc" -mrp -c "$src/$item.S" -o "$out/$item.o"
done
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -DACCELE_TERMINAL="${ACCELE_TERMINAL:-0}" -DACCELE_TERMINAL_TEST="${ACCELE_TERMINAL_TEST:-0}" \
  -DACCELE_SERVICE="${ACCELE_SERVICE:-0}" -D__rtems__ -DUSE_INLINES -DDOOM_FPS_FRAMES="${DOOM_FPS_FRAMES:-1}" \
  -DDOOM_PERSISTENT="${DOOM_PERSISTENT:-0}" \
  -DDOOM_REUSABLE="${DOOM_REUSABLE:-0}" \
  -DDOOM_KEY_FIFO_SUPPORT="${DOOM_KEY_FIFO_SUPPORT:-0}" \
  -DDOOM_PRIVATE_CACHE_MAP="${DOOM_PRIVATE_CACHE_MAP:-1}" -I"$rtems_build/include" \
  -I"$(dirname "$rtems_build")/newlib-1.11.0/newlib/libc/include" \
  -I"$repo/loader/segmented" -I"$repo/loader/digest" \
  -c "$src/app.c" -o "$out/app.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding -c "$repo/loader/segmented/arena.c" -o "$out/arena.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding -c "$repo/loader/digest/sha256.c" -o "$out/sha256.o"
"$tools_bin/i960-elf-ld" -T "$src/link.ld" -Map "$out/kernel.map" \
  -o "$out/kernel.elf" "$out/start.o" "$out/app.o" \
  "$out/terminal.o" "$out/timer_isr.o" "$out/cache.o" "$out/arena.o" "$out/sha256.o" "$rtems_build/context.o" \
  "$rtems_build/libc.o" "$rtems_build/librtems-bounded.a"
"$tools_bin/i960-elf-objcopy" -O binary "$out/kernel.elf" "$out/kernel.bin"
"$tools_bin/i960-elf-nm" -n "$out/kernel.elf" > "$out/kernel.symbols"
python3 - "$out" "${DOOM_PERSISTENT:-0}" "${DOOM_PRIVATE_CACHE_MAP:-1}" "${DOOM_REUSABLE:-0}" "${DOOM_KEY_FIFO_SUPPORT:-0}" "${ACCELE_SERVICE:-0}" "${ACCELE_TERMINAL:-0}" "${ACCELE_TERMINAL_TEST:-0}" <<'PY'
from pathlib import Path
import sys,json
p=Path(sys.argv[1]); image=(p/'kernel.bin').read_bytes()
assert len(image)==29*4096,len(image)
(p/'image.bin').write_bytes(image[:20*4096]+b'\xa5'*(9*4096))
(p/'build.json').write_text(json.dumps(dict(card_profile='accele160',
    terminal_schema=int(sys.argv[7]),terminal_test=int(sys.argv[8]),service_schema=int(sys.argv[6]),keyboard_fifo_schema=int(sys.argv[5]),reusable=bool(int(sys.argv[4])),persistent=bool(int(sys.argv[2])),private_cache_map=bool(int(sys.argv[3]))),indent=2)+'\n')
PY
cc -O2 -shared -fPIC "$src/fnv_host.c" -o "$src/fnv_host.so"
sha256sum "$out/kernel.bin" "$out/image.bin" "$src/fnv_host.so"
