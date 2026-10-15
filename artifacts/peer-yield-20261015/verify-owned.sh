#!/bin/bash
set -euo pipefail
cd /home/mit/i960-peer-yield-20261015
r=project3
c=live-owned
python3 "$r/rtems/residentnet/verify.py" --root build3 "$c" > system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build3/freedoom1.wad > wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build3/freedoom1.wad > wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > frame-tamper.json
