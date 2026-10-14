#!/bin/bash
# Run only after the finite owner has exited normally. Never mutates the card.
set -euo pipefail
cd /home/mit/i960-doom-dma-20261014c
python3 - <<'PY'
from pathlib import Path
assert Path('live.log').read_text().rstrip().endswith('Resident network tests passed; module retained until reboot.')
PY
python3 project/rtems/residentnet/verify.py --root . live > system-replay.json
python3 project/rtems/residentnet/verify_play_dma.py live > dma-replay.json
python3 project/rtems/residentnet/tamper_play_dma.py live > tamper-results.json
python3 analyze.py . /home/mit/i960-doom-bulk-20261014/live > analysis.log
python3 journal_costs.py live > journal-costs.json
tar -czf card-evidence.tar.gz live live.log system-replay.json dma-replay.json tamper-results.json measurements.json journal-costs.json analysis.log close_capture.sh
sha256sum card-evidence.tar.gz
