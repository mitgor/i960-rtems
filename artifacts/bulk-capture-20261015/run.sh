#!/bin/bash
set -euo pipefail
cd /home/mit/i960-bulk-capture-20261015
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/live" --pipeline --pipeline-test --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test --port 8087 > live.log 2>&1 < /dev/null &
echo $! > supervisor.pid
