#!/bin/bash
set -euo pipefail
cd /home/mit/i960-wad-dma-20261014
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/bulk" --pipeline --pipeline-test --wad-load-test --wad-dma --port 8087 > bulk.log 2>&1 < /dev/null &
echo $! > bulk-supervisor.pid
cat bulk-supervisor.pid
