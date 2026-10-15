#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
r=project
c=live-masked
python3 "$r/rtems/residentnet/verify.py" --root build "$c" > masked-system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > masked-frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build/freedoom1.wad > masked-wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > masked-profile.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > masked-profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build/freedoom1.wad > masked-wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > masked-frame-tamper.json
