#!/bin/bash
set -euo pipefail
cd /home/mit/i960-flat-20261016
name=$1
build=${2:-build}
c=live-$name
python3 project/rtems/residentnet/verify.py --root "$build" "$c" > "$name-system.json"
python3 project/rtems/residentnet/verify_play_pipeline.py "$c" > "$name-frames.json"
python3 project/rtems/dma/wad_ring/verify.py "$c" --wad "$build/freedoom1.wad" > "$name-wad.json"
python3 project/rtems/dma/wad_ring/verify_profile.py "$c" > "$name-profile.json"
python3 project/rtems/residentnet/test_drain_replay.py --root "$build" "$c" > "$name-drain-tamper.json"
if [ "${3:-full}" = replay ]; then
 echo '{"reused_abba_frame_mutations":24}' > "$name-frame-tamper.json"
else
 python3 project/rtems/dma/pingpong/test_doom_replay.py "$c" > "$name-frame-tamper.json"
fi
