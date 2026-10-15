#!/bin/bash
set -euo pipefail
cd /home/mit/i960-columns-20261015
# No packaging load during a card measurement.
test -s quality-frames.json
sha256sum build/residentnet/kernel.bin build/residentnet-module/dac960auto.ko build/admission/template.bin build-render/residentnet/kernel.bin build-render/residentnet-module/dac960auto.ko build-render/admission/template.bin build-runtime/residentnet/kernel.bin build-runtime/residentnet-module/dac960auto.ko build-runtime/admission/template.bin > accepted-binaries.sha256
tar -czf candidate.tar.gz --exclude='__pycache__' project/game project/rtems project/loader build build-render build-runtime runtime-native native-fast abba-inputs.tar.gz build.sh run.sh verify.sh archive.sh runtime-card.sh runtime-native.sh native.py columns-oracle.log native.log fast-native.log fast-ram-audit.json fast-admit.log fast-pack.log fast-kernel.log fast-transport.log fast-module.log render-engine-host.log render-engine-cross.log fast-platform-host.log fast-platform-cross.log runtime-native-build.log runtime-native-test.log runtime-native-test-final.log runtime-card-build.log runtime-card-platform.log runtime-card-pack.log runtime-card-pack-first-attempt.log runtime-card-admit.log runtime-card-kernel.log runtime-card-ram.json runtime-card-transport.log runtime-card-module.log accepted-binaries.sha256
sha256sum candidate.tar.gz > candidate.tar.gz.sha256
