#!/bin/bash
set -euo pipefail
# Run from repository root; directory must contain extracted build/ and captures.
evidence=${1:?Extract build-evidence-v1, card-evidence-v1, source-level, card-evidence-level in that order and pass the directory}
wad=${2:?Pass the pinned freedoom1.wad}
for capture in live live-level; do
 python3 rtems/residentnet/verify.py --root "$evidence/build" "$evidence/$capture"
 python3 rtems/residentnet/verify_play_pipeline.py "$evidence/$capture"
 python3 rtems/dma/verify_wad.py "$evidence/$capture" --wad "$wad"
 python3 rtems/dma/pingpong/test_doom_replay.py "$evidence/$capture"
done
python3 artifacts/doom-pingpong-20261015/analyze.py "$evidence/live-level" --native "$evidence/native-frames"
