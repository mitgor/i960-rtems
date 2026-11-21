#!/usr/bin/env bash
# Bounded Doom acceptance under the volatile stock-card handler. No flash write.
set -euo pipefail
bundle=/home/mit/i960-shutdown-safe-20261018/default-bundle
volatile=/home/mit/i960-volatile-handler-20261121
exec /usr/bin/python3 "$bundle/project/rtems/accele160/doom_dma/run_bridge_volatile_stock.py" \
  --persistent --reusable --max-frames 40 --capture-all \
  --port 8089 --keyboard-mode fifo --card-fnv off --paired-frames 4 \
  --fps-manifest "$bundle/project/rtems/accele160/doom_dma/persistent-manifest.json" \
  --startup-oracle "$bundle/inputs/native-requests.bin" \
  --engine-manifest "$bundle/engine/manifest.json" \
  --dma-module "$bundle/inputs/dma_frames.ko" \
  --kernel "$bundle/kernel/kernel.bin" \
  --image "$bundle/kernel/image.bin" \
  --handler "$volatile/handler.bin" \
  --stub "$volatile/stock_ram_even_copy.bin" \
  --install-receipt "$volatile/install-live/result.json" \
  --firmware "$volatile/read0/data.bin" \
  --template "$bundle/engine/template.bin" \
  --relocations "$bundle/engine/relocations.bin" \
  --wad "$bundle/inputs/freedoom1.wad" \
  --readback0 "$volatile/read0" --readback1 "$volatile/read1" \
  --reserve-module "$bundle/inputs/reserve_command.ko" \
  --release-module "$bundle/inputs/release_command.ko" \
  --copy-module "$bundle/inputs/copy_command.ko" \
  --digest-module "$bundle/inputs/digest_command.ko" \
  --admit-module "$bundle/inputs/admit_command.ko" \
  --out "$volatile/doom-live"
