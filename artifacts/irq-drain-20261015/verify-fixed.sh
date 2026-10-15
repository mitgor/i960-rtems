#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
r=project-fixed
c=live-fixed
python3 "$r/rtems/residentnet/verify.py" --root build-fixed "$c" > fixed-system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > fixed-frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build-fixed/freedoom1.wad > fixed-wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > fixed-profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > fixed-profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build-fixed/freedoom1.wad > fixed-wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > fixed-frame-tamper.json
