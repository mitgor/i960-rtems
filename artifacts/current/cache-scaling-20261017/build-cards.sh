#!/usr/bin/env bash
set -euo pipefail
root=/home/mit/i960-cache-scaling-20261017
p=$root/project
cp "$root/admission/engine_identity.h" "$p/rtems/accele160/doom_dma/engine_identity.h"
DOOM_FPS_FRAMES=32 bash "$p/rtems/accele160/doom_dma/build.sh" /home/mit/i960-accele160-rtems-20261017/accele160 /home/mit/i960/tools/bin "$root/new-kernel"
python3 "$p/rtems/accele160/doom_dma/write_manifest.py" "$p/rtems/accele160/doom_dma" "$root/new-kernel" "$root/admission/manifest.json" /home/mit/i960-accele160-doom-dma-20261017-module/dma_frames.ko
mkdir -p "$root/old-build-v2"
cp -a /home/mit/i960-span-four-20261016/build/sources "$root/old-build-v2/"
mkdir -p "$root/old-build-v2/admission"
cp -a "$root/admission/." "$root/old-build-v2/admission/"
test -e "$root/old-build-v2/freedoom1.wad" || ln -s /home/mit/i960-span-four-20261016/build/freedoom1.wad "$root/old-build-v2/freedoom1.wad"
python3 "$p/rtems/build.py" --work "$root/old-build-v2" --cross /home/mit/i960/tools/bin/i960-coff- --profile residentnet --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared --queue-reclaim --owned-mib 12 --resident-upload --doom-heap --doom-shared --doom-runtime --doom-engine "$root/old-build-v2/admission" --wad-batch --wad-poll --dispatch-atomic --doom-dma --wad-ring --wad-profile --peer-yield > "$root/old-kernel.log"
python3 "$p/rtems/residentnet/ram_audit.py" "$root/old-build-v2/residentnet" > "$root/old-ram-audit.json"
python3 "$p/rtems/residentnet/build_transport.py" --payload "$root/old-build-v2/residentnet/kernel.bin" --out "$root/old-build-v2/residentnet-module" > "$root/old-transport.log"
make -C /lib/modules/"$(uname -r)"/build M="$root/old-build-v2/residentnet-module" modules > "$root/old-module.log"
