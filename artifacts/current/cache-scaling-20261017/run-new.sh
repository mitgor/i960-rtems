#!/usr/bin/env bash
set -euo pipefail
root=/home/mit/i960-cache-scaling-20261017
p=$root/project
inputs=/home/mit/i960-accele160-residentworkers-20261017/inputs
exec sudo -n python3 "$p/rtems/accele160/doom_dma/run_bridge.py" \
 --frames 32 --stall-generation 8 --card-fnv off --engine-manifest "$root/admission/manifest.json" \
 --dma-module /home/mit/i960-accele160-doom-dma-20261017-module/dma_frames.ko --port 8087 \
 --fps-manifest "$p/rtems/accele160/doom_dma/live-32-manifest.json" \
 --startup-oracle "$p/artifacts/current/accele160-doom-first-frame-20261017/native-requests.bin" \
 --reserve-module "$inputs/reserve_command.ko" --release-module "$inputs/release_command.ko" \
 --copy-module "$inputs/copy_command.ko" --digest-module "$inputs/digest_command.ko" \
 --admit-module "$inputs/admit_command.ko" --handler "$inputs/handler.bin" --firmware "$inputs/candidate.bin" \
 --kernel "$root/new-kernel/kernel.bin" --image "$root/new-kernel/image.bin" \
 --readback0 "$root/post-v1-0" --readback1 "$root/post-v1-1" \
 --template "$root/admission/template.bin" --relocations "$root/admission/relocations.bin" \
 --wad /home/mit/i960-runtime-entry-20261012/freedoom1.wad --out "$root/new-v2-run"
