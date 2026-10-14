#!/bin/bash
set -euo pipefail
cd /home/mit/i960-dma-owned-20261014
python3 project/rtems/dma/test_target.py
python3 project/rtems/dma/test_host.py
python3 project/rtems/build.py --work "$PWD" --profile residentnet \
 --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
 --queue-reclaim --owned-mib 12 --dispatch-atomic --dma-proof > build.log 2>&1
python3 project/rtems/residentnet/ram_audit.py residentnet > ram-audit.json
python3 project/rtems/residentnet/build_transport.py --payload residentnet/kernel.bin --out residentnet-module > transport-build.log 2>&1
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules > module-build.log 2>&1
