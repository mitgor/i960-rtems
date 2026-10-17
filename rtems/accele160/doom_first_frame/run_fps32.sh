#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 5 ]]; then
  echo "usage: $0 PROJECT_ROOT BUILD_DIR OUTPUT_DIR READBACK0 READBACK1" >&2
  exit 2
fi
project=$(cd "$1" && pwd)
build=$(cd "$2" && pwd)
output=$3
readback0=$4
readback1=$5
inputs=/home/mit/i960-accele160-residentworkers-20261017/inputs
bridge=/home/mit/i960-accele160-riptrace-20261017-inputs
test ! -e "$output"
sudo python3 "$project/rtems/accele160/doom_first_frame/run_bridge.py" \
  --frames 32 \
  --fps-manifest "$project/rtems/accele160/doom_first_frame/fps-32-manifest.json" \
  --startup-oracle "$project/rtems/accele160/doom_first_frame/native-requests.bin" \
  --reserve-module "$inputs/reserve_command.ko" \
  --release-module "$inputs/release_command.ko" \
  --copy-module "$inputs/copy_command.ko" \
  --digest-module "$inputs/digest_command.ko" \
  --admit-module "$inputs/admit_command.ko" \
  --handler "$inputs/handler.bin" \
  --firmware "$inputs/candidate.bin" \
  --kernel "$build/kernel.bin" \
  --image "$build/image.bin" \
  --readback0 "$readback0" \
  --readback1 "$readback1" \
  --template "$bridge/template.bin" \
  --relocations "$bridge/relocations.bin" \
  --wad /home/mit/i960-runtime-entry-20261012/freedoom1.wad \
  --out "$output"
