#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-copy-20261015
r=project2
c=live-copy
python3 "$r/rtems/residentnet/verify.py" --root build2 "$c" > system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build2/freedoom1.wad > wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build2/freedoom1.wad > wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > frame-tamper.json
