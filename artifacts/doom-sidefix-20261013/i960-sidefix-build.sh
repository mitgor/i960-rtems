#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-sidefix-20261013
P=$PWD/project
N=$PWD/newlib-1.11.0
S=doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric
C=/home/mit/i960/tools/bin/i960-coff-
WAD=/home/mit/i960-doom-batch-20261012/freedoom1.wad
for target in host32 i960; do
 if [ "$target" = host32 ]; then name=host; san=--sanitize; else name=cross; san=; fi
 python3 "$P/game/doom/build.py" --work "$PWD/engine-$name" --archive /home/mit/i960-doom-platform-20261012/doomgeneric-source.tar.gz --target "$target" --newlib "$N" --arena-runtime --wad-cache --platform-runtime --startup --checkpoints --point-side-o0 $san > "engine-$name.log" 2>&1
 python3 "$P/game/doom/runtime/platform/build.py" --newlib "$N" --out "$PWD/platform-$name" --doom "$PWD/engine-$name/$S" --engine "$PWD/engine-$name/$target/doom-engine.o" --target "$target" --startup --checkpoints $san > "platform-$name.log" 2>&1
 done
python3 "$P/game/doom/runtime/startup/test_native.py" --build "$PWD/platform-host" --newlib "$N" --wad "$WAD" > native.log 2>&1
python3 "$P/game/doom/runtime/platform/pack_engine.py" --build "$PWD/platform-cross" --out "$PWD/packed" --cross "$C" > packed.log 2>&1
python3 "$P/game/doom/runtime/engine/admit.py" "$PWD/packed" --build "$PWD/platform-cross" --out "$PWD/admission" --startup-oracle /home/mit/i960-doom-sidefix-20261013/host-oracle.json --startup-requests "$PWD/platform-host/startup-0.requests.bin" --startup-checkpoints "$PWD/platform-host/startup-0.checkpoints.bin" --checkpoint-barriers --cross "$C" > admission.log 2>&1
python3 "$P/game/doom/runtime/startup/test_abi.py" --doom "$PWD/engine-cross/$S" --newlib "$N" --out "$PWD/abi-proof" --cross "$C" > abi.log 2>&1
python3 "$P/game/doom/runtime/startup/verify_checkpoints_host.py" "$PWD" --baseline /home/mit/i960-doom-startup-20261013/platform-host --output "$PWD/host-check.json" > host-check.log 2>&1
python3 "$P/rtems/residentnet/test_engine_gate.py" "$PWD/admission" > gate-native.log 2>&1
python3 "$P/rtems/build.py" --work "$PWD" --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$PWD/admission" --wad-batch --wad-poll --dispatch-atomic > kernel-build.log 2>&1
python3 "$P/rtems/residentnet/ram_audit.py" "$PWD/residentnet" > ram-audit.json
python3 "$P/rtems/residentnet/build_transport.py" --payload "$PWD/residentnet/kernel.bin" --out "$PWD/residentnet-module" > module.log 2>&1
make -C /lib/modules/$(uname -r)/build M="$PWD/residentnet-module" modules >> module.log 2>&1
printf 'BUILD AND NATIVE CHECKS PASSED\n'
