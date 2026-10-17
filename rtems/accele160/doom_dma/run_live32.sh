#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 5 && $# != 6 ]]; then
  echo "usage: $0 PROJECT_ROOT BUILD_DIR OUTPUT_DIR READBACK0 READBACK1 [HTTP_PORT]" >&2
  exit 2
fi
project=$(cd "$1" && pwd)
build=$(cd "$2" && pwd)
output=$3
readback0=$4
readback1=$5
port=${6:-0}
inputs=/home/mit/i960-accele160-residentworkers-20261017/inputs
bridge=/home/mit/i960-span-four-20261016/build/admission
test ! -e "$output"
sudo -n python3 "$project/rtems/accele160/doom_dma/run_bridge.py" \
  --frames 32 --stall-generation 8 --card-fnv "${CARD_FNV:-on}" \
  --engine-manifest "$bridge/manifest.json" \
  --dma-module /home/mit/i960-accele160-doom-dma-20261017-module/dma_frames.ko \
  --port "$port" \
  --fps-manifest "$project/rtems/accele160/doom_dma/live-32-manifest.json" \
  --startup-oracle "$project/artifacts/current/accele160-doom-first-frame-20261017/native-requests.bin" \
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
