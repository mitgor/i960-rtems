#!/usr/bin/env bash
set -euo pipefail
root=/home/mit/i960-cache-scaling-20261017
project=$root/project
base=/home/mit/i960-span-four-20261016/build
cross=/home/mit/i960/tools/bin/i960-coff-
for target in i960 host32; do
 suffix=cross; extra=()
 if [[ $target == host32 ]]; then suffix=host; extra=(--sanitize); fi
 python3 "$project/game/doom/runtime/platform/build.py" --newlib "$base/newlib-1.11.0" \
 --out "$root/platform-$suffix" --doom "$base/engine-$suffix/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" \
 --engine "$base/engine-$suffix/$target/doom-engine.o" --target "$target" --cross "$cross" \
 --startup --checkpoints --visible --play --double-buffer --wad-profile --frame-profile \
 --no-fnv --direct-frame --low-detail --cpu-profile --cache-bench "${extra[@]}" > "$root/platform-$suffix.log"
done
python3 "$project/game/doom/runtime/platform/pack_engine.py" --build "$root/platform-cross" --out "$root/packed" --cross "$cross" > "$root/pack.log"
python3 "$project/game/doom/runtime/engine/admit.py" "$root/packed" --build "$root/platform-cross" --out "$root/admission" --play --pingpong --cross "$cross" > "$root/admission.log"
python3 "$project/game/doom/play/test_native.py" --build "$root/platform-host" --newlib "$base/newlib-1.11.0" --wad "$base/freedoom1.wad" > "$root/native.log"
