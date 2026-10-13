#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-visible-20261013
grep -q 'REPLAYS COMPLETE' postrun.log
test ! -d /proc/59894
sudo dmesg > dmesg-final.txt
# Exact candidate binaries/native proofs are in the separately hashed build archive.
tar -czf card-evidence.tar.gz project live live.log boot-id.txt dmesg-final.txt status.py live.sh postrun.sh build.sh archive.sh serve-browser.sh restore.sh build-evidence.sha256 network-replay.json upload-replay.json upload-replay.log checkpoint-comparison.json checkpoint-replay.log startup-evidence-mutations.json startup-evidence-tests.log frame-evidence-card-mutations.json frame-evidence-card-tests.log browser-http-first.json browser-http-final.json first-frame-readback-timing.json frame-readback.json browser-http.log postrun.log
sha256sum card-evidence.tar.gz > card-evidence.sha256
