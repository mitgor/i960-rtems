#!/bin/bash
set -euo pipefail
cd /home/mit/i960-bulk-capture-20261015
r=project
c=live
python3 "$r/rtems/residentnet/verify.py" --root build "$c" > system.json
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$c" > frames.json
python3 "$r/rtems/dma/wad_ring/verify.py" "$c" --wad build/freedoom1.wad > wad.json
python3 "$r/rtems/dma/wad_ring/verify_profile.py" "$c" > profile.json
python3 "$r/rtems/residentnet/test_drain_replay.py" --root build "$c" > drain-tamper.json
python3 "$r/rtems/dma/wad_ring/test_profile_replay.py" "$c" > profile-tamper.json
python3 "$r/rtems/dma/wad_ring/tamper_capture.py" "$c" --wad build/freedoom1.wad > wad-tamper.json
python3 "$r/rtems/dma/pingpong/test_doom_replay.py" "$c" > frame-tamper.json
python3 "$r/rtems/dma/pingpong/test_bulk_replay.py" "$c" > bulk-tamper.log
