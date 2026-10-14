#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/mailbox" --pipeline --pipeline-test --wad-load-test --port 8087 > mailbox.log 2>&1 < /dev/null &
echo $! > mailbox-supervisor.pid
cat mailbox-supervisor.pid
