#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
r=project-stress-masked
c=live-stress-masked
python3 "$r/rtems/residentnet/verify.py" --root build-stress-masked "$c" > stress-masked-system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > stress-masked-frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build-stress-masked/freedoom1.wad > stress-masked-wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > stress-masked-profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > stress-masked-profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build-stress-masked/freedoom1.wad > stress-masked-wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > stress-masked-frame-tamper.json
