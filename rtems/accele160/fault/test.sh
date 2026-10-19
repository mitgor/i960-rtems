#!/usr/bin/env bash
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
for test in policy card owned; do
 cc -Wall -Wextra -Werror -fsanitize=address,undefined "$src/test_$test.c" -o "$work/$test"
 "$work/$test"
done
cc -Wall -Wextra -Werror -fsanitize=address,undefined -DACCELE_TERMINAL_TEST=4 "$src/test_owned.c" -o "$work/nmi"
"$work/nmi"
cc -Wall -Wextra -Werror -fsanitize=address,undefined -DACCELE_TERMINAL_TEST=5 "$src/test_owned.c" -o "$work/runtime"
"$work/runtime"
cc -Wall -Wextra -Werror -fsanitize=address,undefined -DACCELE_TERMINAL_TEST=14 "$src/test_owned.c" -o "$work/inventory-runtime"
cc -Wall -Wextra -Werror -fsanitize=address,undefined -DACCELE_TERMINAL_TEST=15 "$src/test_owned.c" -o "$work/config-runtime"
"$work/config-runtime"
"$work/inventory-runtime"
cc -Wall -Wextra -Werror -fsanitize=address,undefined "$src/../ownership/test_inventory.c" -o "$work/inventory"
"$work/inventory"
python3 "$src/../ownership/test_inventory.py"
cc -Wall -Wextra -Werror -fsanitize=address,undefined "$src/../ownership/test_qlogic.c" -o "$work/qlogic"
"$work/qlogic"
python3 "$src/../ownership/test_qlogic.py"
for mode in 5 13 14 15; do
 cc -E -P -x assembler-with-cpp -DACCELE_TERMINAL=1 -DACCELE_TERMINAL_TEST=$mode "$src/terminal.S" > "$work/entry-$mode.S"
done
cmp "$work/entry-5.S" "$work/entry-14.S"
cmp "$work/entry-5.S" "$work/entry-15.S"
python3 - "$work" <<'CHECK_ENTRY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
assert 'ld 0x1404' not in (p/'entry-14.S').read_text()
assert 'ld 0x1404' in (p/'entry-13.S').read_text()
print('profile 14 exception entry equals profile 5; diagnostic CSR read restricted to 6..13')
CHECK_ENTRY
python3 "$src/test_host.py"

# The actual DMA diagnostic uses 32-bit card addresses. Linux non-PIE gives
# this native harness low static addresses without mapping hardware memory.
if [[ $(uname -s) == Linux && $(uname -m) == x86_64 ]]; then
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/dma"
 "$work/dma"
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -DACCELE_TERMINAL_TEST=8 -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/stall"
 "$work/stall"
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -DACCELE_TERMINAL_TEST=10 -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/resume"
 "$work/resume"
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -DACCELE_TERMINAL_TEST=11 -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/nmi-resume"
 "$work/nmi-resume"
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -DACCELE_TERMINAL_TEST=12 -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/refusal"
 "$work/refusal"
 cc -O1 -no-pie -fsanitize=undefined -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast \
  -DACCELE_TERMINAL_TEST=13 -I"$src/../doom_dma" "$src/test_dma.c" -o "$work/nmi-refusal"
 "$work/nmi-refusal"
fi
