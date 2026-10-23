#!/bin/sh
# Installed in the build directory by deploy.py. Foreground, Ctrl-C to restore.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${I960_BDF:?set I960_BDF to the explicitly identified DAC960PG PCI BDF}"
exec sudo -n python3 "$base/project/rtems/transport/relay.py" \
  --bdf "$I960_BDF" --payload "$base/net/kernel.bin" --module "$base/module/dac960rtems.ko" \
  --output "$base/sessions/$(date -u +%Y%m%d-%H%M%S)" --serve "$@"
