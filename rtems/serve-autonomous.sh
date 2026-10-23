#!/bin/sh
# Installed beside autonet/ and its image-pinned module directory.
# Stop normally with Ctrl-C or systemctl stop; kernel release stops the timer.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${I960_BDF:?set I960_BDF to the explicitly identified DAC960PG PCI BDF}"
module=${I960_AUTONOMOUS_MODULE:-"$base/autonet-module-system-info/dac960auto.ko"}
payload=${I960_AUTONOMOUS_PAYLOAD:-"$base/autonet/kernel.bin"}
exec sudo -n python3 "$base/project/rtems/transport/relay.py" \
 --bdf "$I960_BDF" --payload "$payload" --module "$module" --autonomous \
 --visitor-log "$base/visitor-statistics" \
 --output "$base/sessions/$(date -u +%Y%m%d-%H%M%S)" --serve "$@"
