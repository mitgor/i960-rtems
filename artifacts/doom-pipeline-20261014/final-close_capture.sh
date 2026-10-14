#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-pipeline-20261014c
python3 - <<'PY'
from pathlib import Path
assert 'Resident network tests passed; module retained until reboot.' in Path('live.log').read_text()
PY
python3 project/rtems/residentnet/verify.py --root build live > system-replay.json
python3 project/rtems/residentnet/verify_play_pipeline.py live > pipeline-replay.json
python3 project/rtems/residentnet/tamper_play_pipeline.py live > tamper-results.json
python3 analyze.py . > analysis.log
python3 journal_costs.py live > journal-costs.json
tar --exclude=__pycache__ --exclude=project/artifacts --exclude=build/sources --exclude=build/newlib-1.11.0 --exclude=build/freedoom1.wad -czf build-evidence.tar.gz project build/residentnet build/residentnet-module build/admission build/ram-audit.json native-52 native-52.log host-regression.log live.sh
tar -czf card-evidence.tar.gz live live.log system-replay.json pipeline-replay.json tamper-results.json measurements.json analysis.log journal-costs.json close_capture.sh
sha256sum build-evidence.tar.gz card-evidence.tar.gz
