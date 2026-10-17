#!/usr/bin/env bash
set -euo pipefail
prior=/home/mit/i960-cache-scaling-20261017
work=/home/mit/i960-cache-map-20261018
p=$prior/project
inputs=/home/mit/i960-accele160-residentworkers-20261017/inputs
exec sudo -n python3 "$p/rtems/accele160/doom_dma/run_bridge.py" \
 --frames 32 --stall-generation 8 --card-fnv off \
 --engine-manifest "$prior/admission/manifest.json" \
 --dma-module /home/mit/i960-accele160-doom-dma-20261017-module/dma_frames.ko \
 --port 8087 --fps-manifest "$p/rtems/accele160/doom_dma/live-32-manifest.json" \
 --startup-oracle "$p/artifacts/current/accele160-doom-first-frame-20261017/native-requests.bin" \
 --reserve-module "$inputs/reserve_command.ko" --release-module "$inputs/release_command.ko" \
 --copy-module "$inputs/copy_command.ko" --digest-module "$inputs/digest_command.ko" \
 --admit-module "$inputs/admit_command.ko" --handler "$inputs/handler.bin" \
 --firmware "$inputs/candidate.bin" --kernel "$work/kernel/kernel.bin" \
 --image "$work/kernel/image.bin" --readback0 "$prior/post-v2-0" \
 --readback1 "$prior/post-v2-1" --template "$prior/admission/template.bin" \
 --relocations "$prior/admission/relocations.bin" \
 --wad /home/mit/i960-runtime-entry-20261012/freedoom1.wad --out "$work/run"
