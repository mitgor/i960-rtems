#!/bin/bash
set -euo pipefail
cd /home/mit/i960-point-side-20261016
python3 check_builds.py "$PWD" > build-checks.json
for b in build build-fast; do
 /home/mit/i960/tools/bin/i960-coff-objdump -dr "$b/engine-cross/i960/r_point_side.o" > "$b/point-side.disassembly.txt"
 /home/mit/i960/tools/bin/i960-coff-nm "$b/engine-cross/i960/doom-engine.o" > "$b/engine-symbols.txt"
 sha256sum "$b/residentnet/kernel.bin" "$b/residentnet-module/dac960auto.ko" "$b/admission/template.bin"
done > accepted-binaries.sha256
tar -czf candidate.tar.gz --exclude='__pycache__' --exclude='candidate.tar.gz.sha256' --exclude='restore-relay.log' project/game project/rtems project/host project/loader project/artifacts/doom-m1-20261011/doomgeneric-source.tar.gz project/artifacts/software-loader-20261010/target/runner.bin build build-fast native-baseline native-fast logs-baseline logs-fast setup-errors *.sh *.py *.json *.log *.sha256
sha256sum candidate.tar.gz > candidate.tar.gz.sha256
