#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-dma-fixed-20261014
# Only after complete archives were copied and hash-verified locally and rebooted.
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
cat /proc/sys/kernel/random/boot_id > restored-boot-id.txt
sudo nohup python3 /home/mit/i960-rtems-web-20261011/project/rtems/transport/relay.py \
 --payload /home/mit/i960-rtems-web-20261011/autonet/kernel.bin \
 --module /home/mit/i960-rtems-web-20261011/autonet-module-system-info/dac960auto.ko \
 --autonomous --visitor-log /home/mit/i960-rtems-web-20261011/visitor-statistics \
 --output /home/mit/i960-rtems-web-20261011/http-after-doom-dma-fixed-20261014 \
 --serve --internet6 --publish-http6 2a02:8106:40:9000:f662:19ee:dbad:1f1e --http-port 8080 \
 > restore-relay.log 2>&1 < /dev/null &
echo $! > restored-supervisor.pid
cat restored-supervisor.pid
