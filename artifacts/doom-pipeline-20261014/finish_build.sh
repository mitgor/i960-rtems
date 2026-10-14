#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-pipeline-20261014
python3 project/rtems/residentnet/test_double_buffer.py > double-buffer-test.log
python3 project/rtems/dma/test_pipeline_replay.py > pipeline-replay-test.log
python3 project/rtems/residentnet/build_transport.py --payload "$PWD/build/residentnet/kernel.bin" --out "$PWD/build/residentnet-module" > build/transport.log
python3 project/rtems/dma/stress/test_counter.py --generated build/residentnet-module/dac960auto.c > build/counter-test.log
make -C /lib/modules/$(uname -r)/build M="$PWD/build/residentnet-module" modules > build/module.log 2>&1
sha256sum build/residentnet/kernel.bin build/residentnet-module/dac960auto.ko build/admission/template.bin
