#!/bin/bash
# Run after the finite owner has exited with failure; never releases hardware.
set -euo pipefail
cd "${1:?pass isolated workspace}"
if pgrep -f "^python3 project/rtems/residentnet/live.py --payload $PWD/" >/dev/null; then
 echo 'Owner still running; refusing to close capture.' >&2
 exit 1
fi
sudo cat /sys/kernel/debug/dac960auto/result.txt > retained-result.txt
sudo cat /sys/kernel/debug/dac960auto/frame-dma-buffer.bin > retained-frame-dma.bin
sudo cat /sys/kernel/debug/dac960auto/frame-dma-fault.bin > retained-frame-fault.bin
sudo dmesg > retained-dmesg.txt
sudo lspci -s 37:09.1 -vv > retained-pci.txt
sudo python3 read_retained_mu.py > retained-mu.json
cat /proc/sys/kernel/random/boot_id > retained-boot-id.txt
python3 project/rtems/dma/decode_frame_fault.py retained-frame-fault.bin > retained-fault-decoded.json
tar -czf failed-card-evidence.tar.gz live live.log retained-* capture_failure.sh read_retained_mu.py
sha256sum failed-card-evidence.tar.gz
