#!/usr/bin/env bash
set -euo pipefail
root=/home/mit/i960-cache-scaling-20261017
out=$root/accepted-evidence
mkdir -p "$out/old-build/residentnet" "$out/old-build/residentnet-module" "$out/old-build/admission" "$out/source" "$out/failure"
for n in kernel.bin kernel.symbols kernel.map build.json; do
 cp "$root/old-build-v2/residentnet/$n" "$out/old-build/residentnet/$n"
done
for n in dac960auto.c dac960auto.ko; do
 cp "$root/old-build-v2/residentnet-module/$n" "$out/old-build/residentnet-module/$n"
done
for n in template.bin relocations.bin manifest.json engine_identity.h; do
 cp "$root/old-build-v2/admission/$n" "$out/old-build/admission/$n"
done
cp -a "$root/new-v2-case" "$out/new-v2-case"
cp -a "$root/old-run" "$out/old-run"
cp -a "$root/project/game/doom/runtime/platform/build.py" "$root/project/game/doom/runtime/platform/port.c" "$root/project/game/doom/runtime/platform/presentation.h" "$out/source/"
cp -a "$root/project/game/doom/runtime/cache_bench" "$out/source/cache_bench"
cp -a "$root/project/rtems/residentnet/presentation_profile.py" "$root/project/rtems/residentnet/play_client.py" "$out/source/"
cp -a "$root/project/game/doom/runtime/engine/admit.py" "$out/source/"
cp -a "$root/build-engine.sh" "$root/build-cards.sh" "$root/run-new.sh" "$root/run-old.sh" "$out/source/"
cp -a "$root/new-v2-bench.json" "$root/new-v2-replay.json" "$root/new-v1-final-replay.json" "$out/"
cp -a "$root/old-failed-run/frame-dma-001.bin" "$root/old-failed-run/request.json" "$out/failure/"
cp -a "$root/old-run.log" "$out/failure/original-decoder-failure.log"
# Whole-archive hashes and replay are performed on the Mac after transfer.
tar -cJf "$root/accepted.tar.xz" -C "$out" .
sha256sum "$root/accepted.tar.xz"
