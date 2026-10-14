#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
capture=${1:?capture required}
case "$capture" in mailbox|bulk-repeat) ;; *) exit 2;; esac
python3 - "$capture" <<'PY'
import sys
from pathlib import Path
assert 'Resident network tests passed; module retained until reboot.' in Path(sys.argv[1]+'.log').read_text()
PY
python3 project/rtems/residentnet/verify.py --root build "$capture" > "$capture-system-replay.json"
python3 project/rtems/residentnet/verify_play_pipeline.py "$capture" > "$capture-frame-replay.json"
python3 project/rtems/residentnet/tamper_play_pipeline.py "$capture" > "$capture-tamper.json"
if [ "$capture" = bulk-repeat ]; then
 python3 project/rtems/dma/verify_wad.py "$capture" --wad build/freedoom1.wad > "$capture-wad-replay.json"
fi
python3 compare.py . > measurements.json
if [ "$capture" = mailbox ]; then
 tar --exclude=__pycache__ --exclude=project/artifacts -czf final-build.tar.gz project build/residentnet build/residentnet-module build/admission final-ram-audit.json final-kernel-build.log final-transport.log final-module.log final-target-test.log final-host-test.log final-client-test.log double-buffer-regression.log native-levels native-levels.log native_levels.py run-mailbox.sh compare.py close-run.sh
fi
extra=()
if [ "$capture" = bulk-repeat ]; then extra+=("$capture-wad-replay.json"); fi
tar -czf "$capture-card.tar.gz" "$capture" "$capture.log" "$capture-system-replay.json" "$capture-frame-replay.json" "$capture-tamper.json" measurements.json "${extra[@]}"
if [ "$capture" = bulk-repeat ]; then
 tar --exclude=__pycache__ --exclude=project/artifacts -czf bulk-build.tar.gz project build/residentnet build/residentnet-module build/admission build/play-build.json final-ram-audit.json final-kernel-build.log fast-transport.log fast-module.log fast-poll-test.log fast-driver.diff native-levels native-levels.log native_levels.py run-final-bulk.sh run-play.sh compare.py close-run.sh
 sha256sum bulk-build.tar.gz
fi
# WAD completion/source replay is also copied separately for bulk-repeat.
sha256sum final-build.tar.gz "$capture-card.tar.gz"
