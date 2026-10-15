#!/bin/bash
set -euo pipefail
cd /home/mit/i960-fixeddiv-20261016
# Package only after the fourth physical run and all its replays finish.
test -s a2-frame-tamper.json
tar -czf candidate.tar.gz --exclude='__pycache__' project/game project/rtems project/loader build build-fast native-baseline native-fast build.sh run.sh verify.sh archive.sh native.py native-baseline.log native-fast.log build-baseline.log build-candidate.log fast-native.log fast-ram-audit.json fast-admit.log fast-pack.log fast-kernel.log fast-transport.log fast-module.log render-engine-host.log render-engine-cross.log fast-platform-host.log fast-platform-cross.log accepted-binaries.sha256
sha256sum candidate.tar.gz > candidate.tar.gz.sha256
