#!/bin/bash
set -euo pipefail
cd /home/mit/i960-column-20261015
r=$PWD/project;w=$PWD/build;old=/home/mit/i960-detail-20261014/build
python3 "$r/game/doom/runtime/platform/build.py" --newlib "$w/newlib-1.11.0" --out "$w/platform-baseline" --doom "$old/engine-host/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" --engine "$old/engine-host/host32/doom-engine.o" --target host32 --startup --checkpoints --visible --play --double-buffer --frame-profile --no-fnv --direct-frame --cpu-profile --low-detail --sanitize > baseline-platform.log 2>&1
python3 "$r/game/doom/play/test_native.py" --build "$w/platform-baseline" --newlib "$w/newlib-1.11.0" --wad "$w/freedoom1.wad" > baseline-native.log 2>&1
python3 native_frames.py --baseline > baseline-frames.log 2>&1
python3 native_frames.py > native-frames.log 2>&1
