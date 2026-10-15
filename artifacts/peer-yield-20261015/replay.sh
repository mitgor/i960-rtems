#!/bin/bash
set -euo pipefail
# Run from the repository; arguments: extracted candidate/capture root, WAD.
x=$1
wad=$2
python3 rtems/residentnet/verify.py --root "$x/build2" "$x/live-peer"
python3 rtems/residentnet/verify_play_pipeline.py "$x/live-peer"
python3 rtems/dma/wad_ring/verify.py "$x/live-peer" --wad "$wad"
python3 rtems/dma/wad_ring/verify_profile.py "$x/live-peer"
python3 rtems/dma/wad_ring/test_profile_replay.py "$x/live-peer"
python3 rtems/dma/wad_ring/tamper_capture.py "$x/live-peer" --wad "$wad"
python3 rtems/dma/pingpong/test_doom_replay.py "$x/live-peer"
