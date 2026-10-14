#!/bin/bash
set -euo pipefail
cd /home/mit/i960-present-20261014
capture=${1:?}
case "$capture" in compare) r=project;w=build;n=native-frames;; repeat) r=project-final;w=build-final;n=native-frames-final;; *) exit 2;; esac
python3 - "$capture" <<'PY'
from pathlib import Path
import sys
assert 'Resident network tests passed; module retained until reboot.' in Path(sys.argv[1]+'.log').read_text()
PY
python3 "$r/rtems/residentnet/verify.py" --root "$w" "$capture" > "$capture-system.json"
python3 "$r/rtems/residentnet/verify_play_pipeline.py" "$capture" > "$capture-frames.json"
python3 "$r/rtems/dma/verify_wad.py" "$capture" --wad "$w/freedoom1.wad" > "$capture-wad.json"
python3 "$r/rtems/residentnet/tamper_play_pipeline.py" "$capture" > "$capture-tamper.json"
python3 - <<'PY'
import tarfile
from pathlib import Path
p=Path('previous-frames');p.mkdir(exist_ok=True)
with tarfile.open('previous-card-evidence.tar.gz') as t:
 for i in range(1,53):(p/f'play-0-{i}.bin').write_bytes(t.extractfile(f'live/play-0-{i}.bin').read())
PY
python3 analyze.py "$capture" --native "$n" --previous previous-frames > "$capture-measurements.json"
tar --exclude=__pycache__ --exclude="$r/artifacts" -czf "$capture-build.tar.gz" "$r" "$w/residentnet" "$w/residentnet-module" "$w/admission" "$w/packed" "$w/platform-host" "$w/platform-cross" "$w/engine-host" "$w/engine-cross" "$n" *.sh *.py *.log *ram-audit.json selector-fixed-disassembly.txt
# Logs above include the interrupted first host-module build; no card run used it.
tar -czf "$capture-card.tar.gz" "$capture" "$capture.log" "$capture-system.json" "$capture-frames.json" "$capture-wad.json" "$capture-tamper.json" "$capture-measurements.json"
sha256sum "$capture-build.tar.gz" "$capture-card.tar.gz"
