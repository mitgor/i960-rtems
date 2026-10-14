#!/bin/bash
# Host-only diagnostic build; deliberately preserve the exact old target.
set -euo pipefail
cd /home/mit/i960-doom-dma-repro-20261014
printf '%s  %s\n' d0f89f2dd509d1ed26d3b4e2213d6437f09e63d9127c6e0e462fce7ee3ad3ce4 residentnet/kernel.bin | sha256sum -c -
python3 project/rtems/residentnet/build_transport.py --payload "$PWD/residentnet/kernel.bin" --out "$PWD/residentnet-module"
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules
sha256sum residentnet/kernel.bin residentnet-module/dac960auto.ko
