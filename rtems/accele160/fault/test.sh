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
