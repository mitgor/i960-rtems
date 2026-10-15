#!/bin/bash
set -euo pipefail
# Run from repository root after extracting all three card archives and both
# candidate archives into one directory. The pinned WAD is already in the repo's
# Freedoom ZIP; pass its extracted path explicitly.
evidence=${1:?Pass extracted evidence directory}
wad=${2:?Pass pinned freedoom1.wad}
for capture in live-ring live-word live-baseline; do
 build=build-word
 if [ "$capture" = live-ring ]; then build=build; fi
 python3 rtems/residentnet/verify.py --root "$evidence/$build" "$evidence/$capture"
 python3 rtems/residentnet/verify_play_pipeline.py "$evidence/$capture"
 if [ "$capture" = live-baseline ]; then
  python3 rtems/dma/verify_wad.py "$evidence/$capture" --wad "$wad"
 else
  python3 rtems/dma/wad_ring/verify.py "$evidence/$capture" --wad "$wad"
 fi
done
python3 artifacts/wad-ring-20261015/analyze.py "$evidence/live-ring" "$evidence/live-word" "$evidence/live-baseline" --native "$evidence/native-frames"
