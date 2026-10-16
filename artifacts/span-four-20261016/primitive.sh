#!/bin/bash
set -euo pipefail
cd /home/mit/i960-span-four-20261016
for mode in two four; do
 flags=(); if [ "$mode" = four ]; then flags=(-DDOOM_SPAN_FOUR); fi
 gcc -m32 -O2 -fno-strict-aliasing -fsanitize=address,undefined "${flags[@]}" project/game/doom/render/test_span.c -o "span-$mode-test"
 "./span-$mode-test"
done
