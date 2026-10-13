#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-visible-20261013
cat /proc/sys/kernel/random/boot_id > boot-id.txt
sudo nohup python3 project/rtems/residentnet/live.py --payload "$PWD/residentnet/kernel.bin" --module "$PWD/residentnet-module/dac960auto.ko" --output "$PWD/live" --resident-upload --doom-heap --doom-shared --doom-runtime --wad /home/mit/i960-doom-batch-20261012/freedoom1.wad --upload-concurrent --owned-mib 12 --heap-shared --queue-reclaim --general-heap --extra-ram --fault-owner --secondary-reset --parallel --ticks 540000 --rounds 75 --round-interval 60 --drop-data > live.log 2>&1 < /dev/null &
echo $!
