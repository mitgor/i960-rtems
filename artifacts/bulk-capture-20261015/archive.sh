#!/bin/bash
set -euo pipefail
cd /home/mit/i960-bulk-capture-20261015
# Run only once the bounded session and verify.sh have finished successfully.
test -s system.json
test -s frames.json
tar -czf candidate.tar.gz project build/residentnet build/residentnet-module build/admission build/packed build/platform-cross build/platform-host build/play-build.json build.sh run.sh verify.sh transport.log module.log host-test.log protection-test.log target-test.log
tar -czf card.tar.gz live live.log system.json frames.json wad.json profile.json drain-tamper.json profile-tamper.json wad-tamper.json frame-tamper.json bulk-tamper.log
sha256sum candidate.tar.gz card.tar.gz > archives.sha256
