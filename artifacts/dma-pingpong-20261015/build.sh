#!/bin/bash
set -euo pipefail
cd /home/mit/i960-pingpong-20261015
r=$PWD/project; w=$PWD/build; cross=/home/mit/i960/tools/bin/i960-coff-
python3 "$r/rtems/dma/stress/build_engine.py" --out "$w/pingpong-engine" --cross "$cross" --pingpong > engine.log 2>&1
python3 "$r/rtems/build.py" --work "$w" --cross "$cross" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$w/pingpong-engine/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma > kernel.log 2>&1
python3 "$r/rtems/residentnet/ram_audit.py" "$w/residentnet" > ram-audit.json
python3 "$r/rtems/residentnet/build_transport.py" --payload "$w/residentnet/kernel.bin" --out "$w/residentnet-module-pingpong-v10" > transport.log 2>&1
make -C "/lib/modules/$(uname -r)/build" M="$w/residentnet-module-pingpong-v10" modules > module.log 2>&1
sha256sum "$w/residentnet/kernel.bin" "$w/residentnet-module-pingpong-v10/dac960auto.ko" "$w/pingpong-engine/admission/template.bin"
