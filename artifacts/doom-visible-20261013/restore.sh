#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-visible-20261013
# Run only after the accepted capture is copied/hash-checked locally and rebooted.
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
cat /proc/sys/kernel/random/boot_id > restored-boot-id.txt
sudo nohup python3 /home/mit/i960-rtems-web-20261011/project/rtems/transport/relay.py \
 --payload /home/mit/i960-rtems-web-20261011/autonet/kernel.bin \
 --module /home/mit/i960-rtems-web-20261011/autonet-module-system-info/dac960auto.ko \
 --autonomous --visitor-log /home/mit/i960-rtems-web-20261011/visitor-statistics \
 --output /home/mit/i960-rtems-web-20261011/http-after-doom-visible-20261013 \
 --serve --internet6 --publish-http6 2a02:8106:40:9000:f662:19ee:dbad:1f1e --http-port 8080 \
 > restore-relay.log 2>&1 < /dev/null &
echo $! > restored-supervisor.pid
nohup bash serve-browser.sh > browser-http-restored.log 2>&1 < /dev/null &
echo $! > restored-gallery.pid
cat restored-supervisor.pid restored-gallery.pid
