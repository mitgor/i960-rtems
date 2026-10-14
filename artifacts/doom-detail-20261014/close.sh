#!/bin/bash
set -euo pipefail
cd /home/mit/i960-detail-20261014
python3 - <<'PY'
from pathlib import Path
assert 'Resident network tests passed; module retained until reboot.' in Path('live.log').read_text()
PY
python3 project/rtems/residentnet/verify.py --root build live > system.json
python3 project/rtems/residentnet/verify_play_pipeline.py live > frames.json
python3 project/rtems/dma/verify_wad.py live --wad build/freedoom1.wad > wad.json
python3 project/rtems/residentnet/tamper_play_pipeline.py live > tamper.json
python3 analyze.py live --native native-frames > measurements.json
tar --exclude=__pycache__ --exclude=project/artifacts -czf build-evidence.tar.gz project build/residentnet build/residentnet-module build/admission build/packed build/platform-host build/platform-cross build/engine-host build/engine-cross native-frames *.sh *.py *.log *ram-audit.json kernel-disassembly.txt
tar -czf card-evidence.tar.gz live live.log system.json frames.json wad.json tamper.json measurements.json
sha256sum build-evidence.tar.gz card-evidence.tar.gz
