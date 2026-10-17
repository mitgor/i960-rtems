#!/usr/bin/env bash
# Exact fresh-boot inventory before the external-resume acceptance run.
set -euo pipefail
base=/home/mit/i960-accele160-dma-external-resume-20261017
root=/home/mit/i960-accele160-dma-transfer-20261017
input=/home/mit/i960-accele160-residentworkers-20261017/inputs
reader=/home/mit/i960-accele160-bulkupload-20261017/rawreader.ko
cd "$root"
for index in 0 1; do
  python3 host/accele160/readimage/read_image.py \
    --bdf 0000:37:09.1 --module "$reader" --selector 9 --length 1048576 \
    --out "$base/evidence/pre-after-reboot-$index"
done
python3 rtems/accele160/dma_inventory_corrected/run_residentworkers.py \
  --reserve-module "$input/reserve_command.ko" \
  --release-module "$input/release_command.ko" \
  --copy-module "$input/copy_command.ko" \
  --digest-module "$input/digest_command.ko" \
  --admit-module "$input/admit_command.ko" \
  --handler "$input/handler.bin" \
  --firmware "$input/candidate.bin" \
  --image "$base/inventory-image.bin" \
  --readback0 "$base/evidence/pre-after-reboot-0" \
  --readback1 "$base/evidence/pre-after-reboot-1" \
  --out "$base/evidence/fresh-inventory"
