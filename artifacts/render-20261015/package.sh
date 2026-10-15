#!/bin/bash
set -euo pipefail
cd /home/mit/i960-render-20261015
# Run only after all four bounded tests finish; no packaging load during gameplay.
test -s a2-frames.json
sha256sum build/residentnet/kernel.bin build/residentnet-module/dac960auto.ko build/admission/template.bin build-render/residentnet/kernel.bin build-render/residentnet-module/dac960auto.ko build-render/admission/template.bin > accepted-binaries.sha256
tar -czf candidate.tar.gz --exclude='__pycache__' \
 project/game project/rtems project/loader build build-render native-fast \
 build.sh run.sh verify.sh archive.sh restore.sh native.py span-test.log \
 native.log native-comparison.json fast-native.log fast-ram-audit.json \
 fast-admit.log fast-pack.log fast-kernel.log fast-transport.log fast-module.log \
 render-engine-host.log render-engine-cross.log fast-platform-host.log \
 fast-platform-cross.log accepted-binaries.sha256 renderer.dis renderer-size.txt
sha256sum candidate.tar.gz > candidate.tar.gz.sha256
