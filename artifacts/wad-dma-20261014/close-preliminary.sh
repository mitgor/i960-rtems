#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
python3 - <<'PY'
from pathlib import Path
assert 'Resident network tests passed; module retained until reboot.' in Path('bulk.log').read_text()
PY
python3 project/rtems/residentnet/verify.py --root build bulk > preliminary-system-replay.json
python3 project/rtems/residentnet/verify_play_pipeline.py bulk > preliminary-frame-replay.json
python3 project/rtems/dma/verify_wad.py bulk --wad build/freedoom1.wad > preliminary-wad-replay.json
python3 project/rtems/residentnet/tamper_play_pipeline.py bulk > preliminary-tamper.json
python3 - <<'PY'
import json
from pathlib import Path
rows=[]
for i in range(1,53):
 a=(Path('bulk')/f'play-0-{i}.bin').read_bytes();b=(Path('native-levels')/f'frame-{i}.bin').read_bytes()
 rows.append(dict(frame=i,pixels=sum(x!=y for x,y in zip(a[:64000],b[:64000])),palette_equal=a[64000:64768]==b[64000:64768],padding_equal=a[64768:]==b[64768:]))
Path('preliminary-native-comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
print(rows)
PY
tar --exclude=__pycache__ --exclude=project/artifacts -czf preliminary-build.tar.gz project build/residentnet build/residentnet-module build/admission ram-audit.json kernel-build.log transport.log module.log native-levels native-levels.log native_levels.py run-bulk.sh close-preliminary.sh
tar -czf preliminary-card.tar.gz bulk bulk.log preliminary-system-replay.json preliminary-frame-replay.json preliminary-wad-replay.json preliminary-tamper.json preliminary-native-comparison.json
sha256sum preliminary-build.tar.gz preliminary-card.tar.gz
