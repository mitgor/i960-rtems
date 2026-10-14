#!/bin/bash
set -euo pipefail
cd /home/mit/i960-column-20261015
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver

python3 - <<'PY'
import hashlib,json
from pathlib import Path
w=Path('build');m=json.loads((w/'play-build.json').read_text());m.update(work=str(w.resolve()),repository=str(Path('project').resolve()))
for key,path in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:m[key]=hashlib.sha256((w/path).read_bytes()).hexdigest()
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
PY
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/live" --pipeline --pipeline-test --wad-dma --port 8087 > live.log 2>&1 < /dev/null &
echo $! > final-supervisor.pid
cat final-supervisor.pid
