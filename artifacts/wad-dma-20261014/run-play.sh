#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
test -f bulk-repeat-card.tar.gz
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/play" --pipeline --no-crc --wad-dma --port 8087 > play.log 2>&1 < /dev/null &
echo $! > play-supervisor.pid
cat play-supervisor.pid
