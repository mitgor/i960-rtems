#!/bin/bash
# Reproduce this transport-only candidate from the accepted October 13 engine.
# A full fresh engine build is available through game/doom/play/build.py.
set -euo pipefail
cd /home/mit/i960-doom-dma-fixed-20261014
P=$PWD/project
python3 "$P/rtems/residentnet/test_play_channel.py"
python3 "$P/rtems/residentnet/test_frame_protocol.py"
python3 "$P/rtems/residentnet/test_bulk_protocol.py"
python3 "$P/rtems/residentnet/test_bulk_poll.py"
python3 "$P/rtems/residentnet/test_play_stop.py"
python3 "$P/rtems/residentnet/test_play_bulk_replay.py"
python3 "$P/rtems/build.py" --work "$PWD" --profile residentnet \
 --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
 --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared \
 --doom-runtime --doom-engine "$PWD/admission" --wad-batch --wad-poll \
 --dispatch-atomic --doom-dma > kernel-build.log 2>&1
python3 "$P/rtems/residentnet/ram_audit.py" residentnet > ram-audit.json
python3 "$P/rtems/residentnet/build_transport.py" \
 --payload "$PWD/residentnet/kernel.bin" --out "$PWD/residentnet-module"
python3 "$P/rtems/dma/stress/test_counter.py" --generated "$PWD/residentnet-module/dac960auto.c"
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules > module-build.log 2>&1
sha256sum residentnet/kernel.bin residentnet-module/dac960auto.ko admission/template.bin
