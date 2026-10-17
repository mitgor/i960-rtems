#!/usr/bin/env bash
set -euo pipefail
project=/home/mit/i960-card-delay-old-20261017-project
build=/home/mit/i960-span-four-20261016/build
output=/home/mit/i960-card-delay-old-20261017-run
test ! -e "$output"
python3 "$project/rtems/transport/card_select.py" --bdf 0000:37:04.1 --profile dac960pg
# Exact previously accepted old-card binaries; the only harness changes select
# the old function explicitly and validate its PCI/subsystem identity.
python3 - "$build" <<'PY'
import hashlib,json,sys
from pathlib import Path
w=Path(sys.argv[1]);m=json.loads((w/'play-build.json').read_text())
for key,file in [('kernel_sha256','residentnet/kernel.bin'),('module_sha256','residentnet-module/dac960auto.ko')]:
 assert hashlib.sha256((w/file).read_bytes()).hexdigest()==m[key]
assert m['kernel_sha256']=='f835a7cf69dd416b418e9991b6ae5fd0ff2d166aedd08a4d77a7839a0375b6bc'
assert m['module_sha256']=='45e2aa3ecf9c46f42648e5ebbd45d8a9e5b8f7af1dca67ca194f474c24f9eb3e'
PY
exec sudo -n python3 "$project/game/doom/play/run.py" --work "$build" --output "$output" --pipeline --pipeline-test --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test --port 8087 --frames 120 --release-schedule priority
