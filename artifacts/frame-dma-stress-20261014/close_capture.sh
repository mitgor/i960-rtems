#!/bin/bash
set -euo pipefail
cd /home/mit/i960-frame-stress-20261014
python3 - <<'PY'
from pathlib import Path
assert Path('live.log').read_text().rstrip().endswith('Resident network tests passed; module retained until reboot.')
PY
python3 project/rtems/residentnet/verify.py --root . live > system-replay.json
python3 project/rtems/dma/stress/verify.py live > stress-replay.json
python3 project/rtems/dma/stress/tamper.py live > tamper-results.json
python3 measure.py live > measurements.json
tar --exclude=__pycache__ -czf fixed-build-evidence.tar.gz project/rtems project/game/doom/runtime stress-engine residentnet residentnet-module engine-build.log kernel-build.log module-build.log ram-audit.json live.sh build.sh fixed-build.log fixed-transport.log generated-counter-test.log
 tar -czf fixed-card-evidence.tar.gz live live.log system-replay.json stress-replay.json tamper-results.json measurements.json measure.py close_capture.sh
sha256sum fixed-build-evidence.tar.gz fixed-card-evidence.tar.gz
