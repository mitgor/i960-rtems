#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-play-20261013b
sudo nohup python3 project/rtems/residentnet/live.py \
 --payload "$PWD/residentnet/kernel.bin" --module "$PWD/residentnet-module/dac960auto.ko" \
 --output "$PWD/live" --resident-upload --doom-heap --doom-shared --doom-runtime \
 --wad /home/mit/i960-doom-batch-20261012/freedoom1.wad \
 --upload-concurrent --owned-mib 12 --heap-shared --queue-reclaim \
 --general-heap --extra-ram --fault-owner --secondary-reset --parallel \
 --ticks 540000 --rounds 1 --play-port 8087 --play-accept-frames 6 --audit-interval 60 \
 > live.log 2>&1 < /dev/null &
echo $! > live-supervisor.pid
cat live-supervisor.pid
