#!/bin/bash
set -euo pipefail
cd /home/mit/i960-pingpong-20261015
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
sudo nohup python3 project/rtems/residentnet/live.py \
 --payload build/residentnet/kernel.bin --module build/residentnet-module-pingpong-v10/dac960auto.ko \
 --output live-v10 --resident-upload --doom-heap --doom-shared --doom-runtime \
 --wad build/freedoom1.wad --upload-concurrent --owned-mib 12 \
 --heap-shared --queue-reclaim --general-heap --extra-ram --fault-owner \
 --secondary-reset --parallel --ticks 540000 --rounds 1 \
 --frame-dma-stress 256 --pingpong --audit-interval 3 \
 > live-v10.log 2>&1 < /dev/null &
echo $! > live.pid
cat live.pid
