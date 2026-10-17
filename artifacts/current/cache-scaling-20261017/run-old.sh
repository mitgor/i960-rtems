#!/usr/bin/env bash
set -euo pipefail
root=/home/mit/i960-cache-scaling-20261017
# Board wrapper independently selects BDF 37:04.1 and exact DAC960PG identity;
# retained new-card resources are left untouched after its test has quiesced.
python3 - "$root" <<'CHECK'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);result=json.loads((r/'new-v2-run/result.json').read_text())
assert result['dma_frames']==32 and result['grant_retained']
for name in ('template.bin','relocations.bin','manifest.json'):
 assert (r/'admission'/name).read_bytes()==(r/'old-build-v2/admission'/name).read_bytes()
CHECK
python3 "$root/project/rtems/transport/card_select.py" --bdf 0000:37:04.1 --profile dac960pg
exec sudo -n python3 "$root/project/game/doom/play/run.py" \
 --work "$root/old-build-v2" --output "$root/old-run" --pipeline --pipeline-test \
 --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test \
 --port 8087 --frames 120 --release-schedule priority
