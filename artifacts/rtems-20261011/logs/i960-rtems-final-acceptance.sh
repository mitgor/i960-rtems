#!/bin/bash
set -eu
base=/home/mit/i960-rtems-final-20261011
while test -e /proc/35967; do sleep 2; done
python3 - <<'PY'
import json
from pathlib import Path
s=json.loads(Path('/home/mit/i960-rtems-20261011/net-stress-30min/summary.json').read_text())
assert s['restored'] and s['unloaded'] and s['steps']>25000
assert Path('/home/mit/i960-rtems-20261011/net-stress-30min/stress-result.json').exists()
assert not Path('/sys/module/dac960rtems').exists()
PY
sudo -n python3 "$base/project/rtems/transport/live_cleanup_test.py" --payload "$base/net/kernel.bin" --module "$base/module/dac960rtems.ko" --output "$base/cleanup-tests"
for mode in 0 1 2 3 4 5 6; do
 case "$mode" in
  0) expected=0x46600001;;
  1) expected=0xf0001234;;
  2) expected=0x46600030;;
  *) expected=$((0x46600000 + mode));;
 esac
 sudo -n python3 "$base/project/host/loadrun/loadrun.py" "$base/bounded/kernel.bin" --module /home/mit/i960-tetris-t3/module/dac960loadrun.ko --output "$base/bounded-mode-$mode" --argument "$mode" --expect "$expected"
done
sudo -n python3 "$base/project/rtems/transport/relay.py" --payload "$base/net/kernel.bin" --module "$base/module/dac960rtems.ko" --output "$base/final-internet" --internet --faults
