#!/bin/bash
set -euo pipefail
cd /home/mit/i960-columns-20261015
# Run only between card tests, never add compiler load to a benchmark.
r=$PWD/project
w=$PWD/build-runtime
if [ ! -d "$w" ]; then cp -a build-render "$w"; fi
cross=/home/mit/i960/tools/bin/i960-coff-
python3 "$r/game/doom/runtime/platform/build.py" --newlib "$w/newlib-1.11.0" --out "$w/platform-cross" --doom "$w/engine-cross/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" --engine "$w/engine-cross/i960/doom-engine.o" --target i960 --startup --checkpoints --visible --play --double-buffer --frame-profile --no-fnv --direct-frame --cpu-profile --low-detail --runtime-detail --wad-profile > runtime-card-platform.log 2>&1
python3 "$r/game/doom/runtime/platform/pack_engine.py" --build "$w/platform-cross" --out "$w/packed" --cross "$cross" > runtime-card-pack.log 2>&1
python3 "$r/game/doom/runtime/engine/admit.py" "$w/packed" --build "$w/platform-cross" --out "$w/admission" --play --pingpong --cross "$cross" > runtime-card-admit.log 2>&1
python3 "$r/rtems/build.py" --work "$w" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$w/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma --wad-ring --wad-profile --peer-yield > runtime-card-kernel.log 2>&1
python3 "$r/rtems/residentnet/ram_audit.py" "$w/residentnet" > runtime-card-ram.json
rm -rf "$w/residentnet-module"
python3 "$r/rtems/residentnet/build_transport.py" --payload "$w/residentnet/kernel.bin" --out "$w/residentnet-module" > runtime-card-transport.log 2>&1
make -C "/lib/modules/$(uname -r)/build" M="$w/residentnet-module" modules > runtime-card-module.log 2>&1
python3 - <<'PY'
import json,hashlib
from pathlib import Path
w=Path('build-runtime');m=json.loads((w/'play-build.json').read_text());m.update(work=str(w.resolve()),runtime_detail=True,fast_columns=True,fast_render=True)
for k,p in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:m[k]=hashlib.sha256((w/p).read_bytes()).hexdigest()
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
PY
