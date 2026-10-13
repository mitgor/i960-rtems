#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-play-20261013b
P=$PWD/project
A=/home/mit/i960-doom-platform-20261012/doomgeneric-source.tar.gz
W=/home/mit/i960-doom-batch-20261012/freedoom1.wad
C=/home/mit/i960/tools/bin/i960-coff-
D=doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric
for spec in host:host32 cross:i960; do
 suffix=${spec%:*}; target=${spec#*:}; extra=()
 if [ "$target" = host32 ]; then extra=(--sanitize); fi
 python3 "$P/game/doom/build.py" --work "$PWD/engine-$suffix" --archive "$A" --target "$target" --newlib "$PWD/newlib-1.11.0" --arena-runtime --wad-cache --platform-runtime --startup --checkpoints --point-side-o0 --visible --play "${extra[@]}" > "engine-$suffix.log" 2>&1
 python3 "$P/game/doom/runtime/platform/build.py" --newlib "$PWD/newlib-1.11.0" --out "$PWD/platform-$suffix" --doom "$PWD/engine-$suffix/$D" --engine "$PWD/engine-$suffix/$target/doom-engine.o" --target "$target" --startup --checkpoints --visible --play "${extra[@]}" > "platform-$suffix.log" 2>&1
done
python3 "$P/game/doom/play/test_native.py" --build "$PWD/platform-host" --newlib "$PWD/newlib-1.11.0" --wad "$W" > native.log
python3 "$P/game/doom/runtime/platform/pack_engine.py" --build "$PWD/platform-cross" --out "$PWD/packed" --cross "$C" > packed.log
python3 "$P/game/doom/runtime/engine/admit.py" "$PWD/packed" --build "$PWD/platform-cross" --out "$PWD/admission" --play --cross "$C" > admission.log
python3 "$P/game/doom/runtime/startup/test_abi.py" --doom "$PWD/engine-cross/$D" --newlib "$PWD/newlib-1.11.0" --out "$PWD/abi-proof" --cross "$C" > abi.log
python3 "$P/rtems/build.py" --work "$PWD" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$PWD/admission" --wad-batch --wad-poll --dispatch-atomic > kernel-build.log 2>&1
python3 "$P/rtems/residentnet/ram_audit.py" residentnet > ram-audit.json
python3 "$P/rtems/residentnet/build_transport.py" --payload "$PWD/residentnet/kernel.bin" --out "$PWD/residentnet-module"
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules > module.log 2>&1
