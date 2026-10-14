#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-pipeline-20261014
sudo nohup python3 project/game/doom/play/run.py --work "$PWD/build" --output "$PWD/live" --pipeline --pipeline-test --port 8087 > live.log 2>&1 < /dev/null &
echo $! > supervisor.pid
cat supervisor.pid
