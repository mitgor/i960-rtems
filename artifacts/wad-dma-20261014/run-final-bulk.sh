#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
# Baseline build/card archives must already be closed, copied and replayed.
test -f mailbox-card.tar.gz
if [ ! -d build/residentnet-module-mailbox ]; then
 mv build/residentnet-module build/residentnet-module-mailbox
 cp -a build/residentnet-module-fast build/residentnet-module
fi
cmp build/residentnet-module-fast/dac960auto.ko build/residentnet-module/dac960auto.ko
python3 - <<'MANIFEST'
import hashlib,json
from pathlib import Path
w=Path('build');m=json.loads((w/'play-build.json').read_text()) if (w/'play-build.json').exists() else dict(pipeline=True,dma=True,wad_sha256=hashlib.sha256((w/'freedoom1.wad').read_bytes()).hexdigest())
m.update(work=str(w.resolve()),repository=str(Path('project').resolve()),wad_dma_supported=True)
for key,path in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:m[key]=hashlib.sha256((w/path).read_bytes()).hexdigest()
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
MANIFEST
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/bulk-repeat" --pipeline --pipeline-test --wad-load-test --wad-dma --port 8087 > bulk-repeat.log 2>&1 < /dev/null &
echo $! > bulk-repeat-supervisor.pid
cat bulk-repeat-supervisor.pid
