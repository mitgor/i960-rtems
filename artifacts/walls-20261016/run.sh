#!/bin/bash
set -euo pipefail
cd /home/mit/i960-walls-20261016
name=$1
case "$name" in p0) build=build-plain;; a1|a2) build=build;; b1|b2) build=build-fast;; *) exit 2;; esac
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
python3 - "$build" <<'PY'
import hashlib,json,sys
from pathlib import Path
w=Path(sys.argv[1]);m=json.loads((Path('build')/'play-build.json').read_text());m.update(work=str(w.resolve()),repository=str(Path('project').resolve()))
admission=json.loads((w/'admission/manifest.json').read_text())
for key in ('wall_profile','fast_walls','fast_point_side','input_trace','fixed_div_profile','fast_fixed_div','fast_render','fast_columns','runtime_detail'):m[key]=bool(admission.get(key))
for key,path in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:m[key]=hashlib.sha256((w/path).read_bytes()).hexdigest()
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
PY
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/$build" --output "$PWD/live-$name" --pipeline --pipeline-test --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test --port 8087 --frames 520 --release-schedule priority > "live-$name.log" 2>&1 < /dev/null &
echo $! > "$name-supervisor.pid"
