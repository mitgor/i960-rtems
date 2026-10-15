#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
r=project-stress-fixed
c=live-stress-fixed
python3 "$r/rtems/residentnet/verify.py" --root build-stress-fixed "$c" > stress-fixed-system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > stress-fixed-frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build-stress-fixed/freedoom1.wad > stress-fixed-wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > stress-fixed-profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > stress-fixed-profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build-stress-fixed/freedoom1.wad > stress-fixed-wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > stress-fixed-frame-tamper.json
