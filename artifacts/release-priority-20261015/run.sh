#!/bin/bash
set -euo pipefail
cd /home/mit/i960-release-priority-20261015
name=$1
case "$name" in abba|baab) ;; *) exit 2;; esac
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
python3 - <<'PY'
import hashlib,json
from pathlib import Path
w=Path('build');m=json.loads((w/'play-build.json').read_text());m.update(work=str(w.resolve()),repository=str(Path('project').resolve()))
assert hashlib.sha256((w/'residentnet/kernel.bin').read_bytes()).hexdigest()=='1dce227e130d144187cfd0577ca333da09d20d62baf6617db30bc29b137a2c08'
assert hashlib.sha256((w/'residentnet-module/dac960auto.ko').read_bytes()).hexdigest()=='e97e8bd9eeb7da15bfb19d62625bb928c2b393e4357cec1bc903abe0f48111d9'
(w/'play-build.json').write_text(json.dumps(m,indent=2)+'\n')
PY
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/live-$name" --pipeline --pipeline-test --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test --port 8087 --frames 520 --release-schedule "$name" > "live-$name.log" 2>&1 < /dev/null &
echo $! > "$name-supervisor.pid"
