#!/bin/bash
set -euo pipefail
cd /home/mit/i960-point-side-20261016
r=$PWD/project
# Seed a fresh work tree from accepted dependencies; never mutate an accepted tree.
w=$PWD/$1
side=(--point-side-o0)
if [ "$1" = build-fast ]; then side=(--fast-point-side); fi
cross=/home/mit/i960/tools/bin/i960-coff-
for pair in host:host32 cross:i960; do
 suffix=${pair%:*}; target=${pair#*:}; extra=()
 if [ "$target" = host32 ]; then extra+=(--sanitize); fi
 python3 "$r/game/doom/build.py" --work "$w/engine-$suffix" --archive "$r/artifacts/doom-m1-20261011/doomgeneric-source.tar.gz" --target "$target" --cross "$cross" --newlib "$w/newlib-1.11.0" --arena-runtime --wad-cache --platform-runtime --wad-profile --startup --checkpoints --visible --play --fast-render --fast-columns "${side[@]}" "${extra[@]}" > "render-engine-$suffix.log" 2>&1
 python3 "$r/game/doom/runtime/platform/build.py" --newlib "$w/newlib-1.11.0" --out "$w/platform-$suffix" --doom "$w/engine-$suffix/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" --engine "$w/engine-$suffix/$target/doom-engine.o" --target "$target" --cross "$cross" --startup --checkpoints --visible --play --double-buffer --frame-profile --no-fnv --direct-frame --cpu-profile --low-detail --wad-profile  "${extra[@]}" > "fast-platform-$suffix.log" 2>&1
done
python3 "$r/game/doom/play/test_native.py" --build "$w/platform-host" --newlib "$w/newlib-1.11.0" --wad "$w/freedoom1.wad" > fast-native.log 2>&1
python3 "$r/game/doom/runtime/platform/pack_engine.py" --build "$w/platform-cross" --out "$w/packed" --cross "$cross" > fast-pack.log 2>&1
python3 "$r/game/doom/runtime/engine/admit.py" "$w/packed" --build "$w/platform-cross" --out "$w/admission" --play --pingpong --cross "$cross" > fast-admit.log 2>&1
python3 "$r/rtems/build.py" --work "$w" --cross "$cross" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$w/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma --wad-ring --wad-profile --peer-yield > fast-kernel.log 2>&1
python3 "$r/rtems/residentnet/ram_audit.py" "$w/residentnet" > fast-ram-audit.json
rm -rf "$w/residentnet-module"
python3 "$r/rtems/residentnet/build_transport.py" --payload "$w/residentnet/kernel.bin" --out "$w/residentnet-module" > fast-transport.log 2>&1
make -C "/lib/modules/$(uname -r)/build" M="$w/residentnet-module" modules > fast-module.log 2>&1
sha256sum "$w/residentnet/kernel.bin" "$w/residentnet-module/dac960auto.ko" "$w/admission/template.bin" > fast-binaries.sha256
