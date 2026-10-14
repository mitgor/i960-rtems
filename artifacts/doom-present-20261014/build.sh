#!/bin/bash
set -euo pipefail
cd /home/mit/i960-present-20261014
r=$PWD/project
w=$PWD/build
cross=/home/mit/i960/tools/bin/i960-coff-
for pair in host:host32 cross:i960; do
 suffix=${pair%:*}; target=${pair#*:}; extra=()
 if [ "$target" = host32 ]; then extra+=(--sanitize); fi
 python3 "$r/game/doom/runtime/platform/build.py" --newlib "$w/newlib-1.11.0" --out "$w/platform-$suffix" --doom "$w/engine-$suffix/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric" --engine "$w/engine-$suffix/$target/doom-engine.o" --target "$target" --cross "$cross" --startup --checkpoints --visible --play --double-buffer --frame-profile --presentation-test "${extra[@]}" > "platform-$suffix.log" 2>&1
done
python3 "$r/game/doom/play/test_native.py" --build "$w/platform-host" --newlib "$w/newlib-1.11.0" --wad "$w/freedoom1.wad" > native-test.log 2>&1
python3 "$r/game/doom/runtime/platform/pack_engine.py" --build "$w/platform-cross" --out "$w/packed" --cross "$cross" > pack.log 2>&1
python3 "$r/game/doom/runtime/engine/admit.py" "$w/packed" --build "$w/platform-cross" --out "$w/admission" --play --cross "$cross" > admit.log 2>&1
python3 "$r/rtems/build.py" --work "$w" --cross "$cross" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$w/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma > kernel.log 2>&1
python3 "$r/rtems/residentnet/ram_audit.py" "$w/residentnet" > ram-audit.json
if [ -d "$w/residentnet-module" ]; then mv "$w/residentnet-module" "$w/residentnet-module-before-profile"; fi
python3 "$r/rtems/residentnet/build_transport.py" --payload "$w/residentnet/kernel.bin" --out "$w/residentnet-module" > transport.log 2>&1
make -C "/lib/modules/$(uname -r)/build" M="$w/residentnet-module" modules > module.log 2>&1
python3 "$r/rtems/residentnet/test_double_buffer.py" > double-buffer.log
python3 "$r/rtems/dma/test_frame_target.py" > frame-target.log 2>&1
python3 "$r/rtems/dma/test_frame_host.py" > frame-host.log 2>&1
python3 "$r/rtems/dma/test_wad_poll.py" --generated "$w/residentnet-module/dac960auto.c" > poll.log
sha256sum "$w/residentnet/kernel.bin" "$w/residentnet-module/dac960auto.ko" "$w/admission/template.bin"
