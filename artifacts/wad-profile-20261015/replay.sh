#!/bin/bash
set -euo pipefail
# Extract candidate.tar.gz, candidate-v2.tar.gz, card-v1.tar.gz and card-v2.tar.gz
# into the same directory. Pass the pinned Freedoom WAD separately.
e=${1:?extracted evidence directory}
wad=${2:?pinned freedoom1.wad}
for pair in build:live-profile2 build2:live-profile3; do
 b=${pair%:*}; c=${pair#*:}
 python3 rtems/residentnet/verify.py --root "$e/$b" "$e/$c"
 python3 rtems/residentnet/verify_play_pipeline.py "$e/$c"
 python3 rtems/dma/wad_ring/verify.py "$e/$c" --wad "$wad"
done
# Historical v1 report has invalid zero cache telemetry; use its exact schema
# only to reproduce the runtime/DMA counters, never claim cache attribution.
python3 "$e/project/rtems/dma/wad_ring/verify_profile.py" "$e/live-profile2"
python3 rtems/dma/wad_ring/verify_profile.py "$e/live-profile3"
python3 rtems/dma/wad_ring/test_profile_replay.py "$e/live-profile3"
python3 artifacts/wad-ring-20261015/analyze.py "$e/live-profile2" "$e/live-profile3" --native "$e/native-frames2"
