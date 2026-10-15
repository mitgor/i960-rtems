#!/bin/bash
set -euo pipefail
# Run from this repository. Argument is an extracted evidence workspace.
evidence=${1:?Pass the workspace containing build/ and live-v10/}
python3 rtems/residentnet/verify.py --root "$evidence/build" "$evidence/live-v10"
python3 rtems/dma/pingpong/verify.py "$evidence/live-v10"
python3 rtems/dma/pingpong/test_replay.py "$evidence/live-v10"
python3 artifacts/dma-pingpong-20261015/analyze.py "$evidence/live-v10"
