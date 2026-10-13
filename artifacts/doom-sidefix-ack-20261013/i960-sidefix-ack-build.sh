#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-sidefix-ack-20261013
P=$PWD/project
python3 "$P/rtems/residentnet/test_checkpoint_barriers.py" > checkpoint-barrier-tests.log
python3 "$P/rtems/build.py" --work "$PWD" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$PWD/admission" --wad-batch --wad-poll --dispatch-atomic > kernel-build.log 2>&1
python3 "$P/rtems/residentnet/ram_audit.py" "$PWD/residentnet" > ram-audit.json
python3 "$P/rtems/residentnet/build_transport.py" --payload "$PWD/residentnet/kernel.bin" --out "$PWD/residentnet-module" > module.log 2>&1
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules >> module.log 2>&1
printf 'BUILD AND NATIVE CHECKS PASSED\n'
