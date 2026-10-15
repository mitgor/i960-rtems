#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
for mode in before after drain drain-reverse; do
 python3 project-fixed/rtems/residentnet/test_general_heap.py --rtems build-fixed/rtems-4.6.6 --out "native-$mode" --shared --queue-reclaim --shutdown-race "$mode"
done
python3 project-fixed/rtems/exclusive/test_peer_yield.py
python3 project-fixed/rtems/residentnet/test_drain.py
