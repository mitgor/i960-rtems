#!/usr/bin/env bash
# Exact 2026-10-17 new-card acceptance: keep recovery adjacent to SIGKILL.
set -u
base=/home/mit/i960-accele160-dma-external-resume-20261017
root=/home/mit/i960-accele160-dma-transfer-20261017
input=/home/mit/i960-accele160-residentworkers-20261017/inputs
prior="$base/evidence/fresh-inventory"
pin=/home/mit/i960-accele160-dma-gate-20261017/host/dma_pin.ko
out="$base/evidence/attempt-2"
cd "$root" || exit 1
python3 rtems/accele160/dma_external_resume/start_and_die.py \
  --reserve-module "$input/reserve_command.ko" \
  --release-module "$input/release_command.ko" \
  --copy-module "$input/copy_command.ko" \
  --digest-module "$input/digest_command.ko" \
  --admit-module "$input/admit_command.ko" \
  --handler "$input/handler.bin" \
  --firmware "$input/candidate.bin" \
  --image "$base/build-fixed/image.bin" \
  --readback0 "$base/evidence/pre-after-reboot-0" \
  --readback1 "$base/evidence/pre-after-reboot-1" \
  --out "$out" --dma-module "$pin" \
  --mode halt --prior-run "$prior" --die-at-held
death_status=$?
if [[ "$death_status" -ne 137 || ! -f "$out/death-intent.json" ]]; then
  echo "starter did not reach the durable death checkpoint; retain resources" >&2
  exit 1
fi
python3 rtems/accele160/dma_external_resume/recover.py \
  --out "$out" --handler "$input/handler.bin" \
  --firmware "$input/candidate.bin" \
  --image "$base/build-fixed/image.bin" --dma-module "$pin" \
  --prior-run "$prior" \
  --readback0 "$base/evidence/pre-after-reboot-0" \
  --readback1 "$base/evidence/pre-after-reboot-1"
