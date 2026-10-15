#!/bin/bash
set -euo pipefail
cd /home/mit/i960-columns-20261015
r=$PWD/project
w=$PWD/build-render
python3 "$r/game/doom/runtime/platform/build.py" --newlib "$w/newlib-1.11.0" --out "$PWD/runtime-native" --doom "$w/engine-host/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" --engine "$w/engine-host/host32/doom-engine.o" --target host32 --startup --checkpoints --visible --play --double-buffer --frame-profile --no-fnv --direct-frame --cpu-profile --low-detail --runtime-detail --wad-profile --sanitize > runtime-native-build.log 2>&1
python3 "$r/game/doom/play/test_native.py" --build "$PWD/runtime-native" --newlib "$w/newlib-1.11.0" --wad "$w/freedoom1.wad" --runtime-detail-test > runtime-native-test.log 2>&1
