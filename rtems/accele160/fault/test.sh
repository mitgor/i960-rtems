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
fi
