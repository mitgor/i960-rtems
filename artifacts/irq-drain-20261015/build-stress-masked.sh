#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
r=$PWD/project-stress-masked
w=$PWD/build-stress-masked
cross=/home/mit/i960/tools/bin/i960-coff-
python3 "$r/rtems/build.py" --work "$w" --cross "$cross" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$w/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma --wad-ring --wad-profile --peer-yield > stress-masked-kernel.log 2>&1
python3 "$r/rtems/residentnet/ram_audit.py" "$w/residentnet" > stress-masked-ram-audit.json
if [ -d "$w/residentnet-module" ]; then mv "$w/residentnet-module" "$w/residentnet-module-before-profile-$(date +%s)"; fi
python3 "$r/rtems/residentnet/build_transport.py" --payload "$w/residentnet/kernel.bin" --out "$w/residentnet-module" > stress-masked-transport.log 2>&1
make -C "/lib/modules/$(uname -r)/build" M="$w/residentnet-module" modules > stress-masked-module.log 2>&1
python3 "$r/rtems/residentnet/test_double_buffer.py" > stress-masked-double-buffer.log
python3 "$r/rtems/dma/test_frame_target.py" > stress-masked-frame-target.log 2>&1
python3 "$r/rtems/dma/test_frame_host.py" > stress-masked-frame-host.log 2>&1
python3 "$r/rtems/dma/test_wad_poll.py" --generated "$w/residentnet-module/dac960auto.c" > stress-masked-poll.log
sha256sum "$w/residentnet/kernel.bin" "$w/residentnet-module/dac960auto.ko" "$w/admission/template.bin"

for t in target host client protection; do python3 "$r/rtems/dma/pingpong/test_$t.py" > "stress-masked-test-pp-$t.log" 2>&1; done
