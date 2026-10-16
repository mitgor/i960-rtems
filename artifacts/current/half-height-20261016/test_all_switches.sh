#!/bin/bash
set -euo pipefail
cd /home/mit/i960-half-20261016
python3 project/game/doom/runtime/platform/build.py \
 --newlib build/newlib-1.11.0 --out native-all-switches/platform \
 --doom build/engine-host/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric \
 --engine build/engine-host/host32/doom-engine.o --target host32 \
 --startup --checkpoints --visible --play --double-buffer --frame-profile \
 --no-fnv --direct-frame --cpu-profile --low-detail --runtime-detail \
 --wad-profile --sanitize > all-switches-build.log 2>&1
python3 project/game/doom/play/test_native.py --runtime-detail-test \
 --runtime-flat-test --runtime-half-height-test --build native-all-switches/platform \
 --newlib build/newlib-1.11.0 --wad build/freedoom1.wad > all-switches-native.log 2>&1
