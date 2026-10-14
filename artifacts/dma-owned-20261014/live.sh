#!/bin/bash
set -euo pipefail
cd /home/mit/i960-dma-owned-20261014
exec sudo python3 project/rtems/residentnet/live.py --payload residentnet/kernel.bin \
 --module residentnet-module/dac960auto.ko --output live --secondary-reset \
 --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim \
 --owned-mib 12 --ticks 60000 --rounds 1 --dma-proof
