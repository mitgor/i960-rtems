#!/bin/bash
set -euo pipefail
cd /home/mit/i960-bulk-capture-20261015
mv build/residentnet-module build/module-before-bulk
python3 project/rtems/residentnet/build_transport.py --payload "$PWD/build/residentnet/kernel.bin" --out "$PWD/build/residentnet-module" > transport.log
make -C "/lib/modules/$(uname -r)/build" M="$PWD/build/residentnet-module" modules > module.log 2>&1
python3 - <<'PY'
import hashlib,json
from pathlib import Path
w=Path('build');m=json.loads((w/'play-build.json').read_text());m.update(work=str(w.resolve()),repository=str(Path('project').resolve()))
for key,path in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:m[key]=hashlib.sha256((w/path).read_bytes()).hexdigest()
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
assert m['kernel_sha256']=='1dce227e130d144187cfd0577ca333da09d20d62baf6617db30bc29b137a2c08'
PY
python3 project/rtems/dma/pingpong/test_host.py > host-test.log 2>&1
sha256sum build/residentnet/kernel.bin build/residentnet-module/dac960auto.ko build/admission/template.bin
