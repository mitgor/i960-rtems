#!/bin/bash
set -euo pipefail
x=$1
mode=$2
wad=$3
if [ "$mode" = masked ]; then b=build; else b=build-$mode; fi
c=$x/live-$mode
python3 rtems/residentnet/verify.py --root "$x/$b" "$c"
python3 rtems/residentnet/verify_play_pipeline.py "$c"
python3 rtems/dma/wad_ring/verify.py "$c" --wad "$wad"
python3 rtems/dma/wad_ring/verify_profile.py "$c"
python3 rtems/residentnet/test_drain_replay.py --root "$x/$b" "$c"
python3 rtems/dma/wad_ring/test_profile_replay.py "$c"
python3 rtems/dma/wad_ring/tamper_capture.py "$c" --wad "$wad"
python3 rtems/dma/pingpong/test_doom_replay.py "$c"
