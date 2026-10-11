#!/bin/sh
# Installed beside autonet/ and its image-pinned module directory.
# Stop normally with Ctrl-C or systemctl stop; kernel release stops the timer.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
module=${I960_AUTONOMOUS_MODULE:-"$base/autonet-module-vader/dac960auto.ko"}
exec sudo -n python3 "$base/project/rtems/transport/relay.py" \
 --payload "$base/autonet/kernel.bin" --module "$module" --autonomous \
 --output "$base/sessions/$(date -u +%Y%m%d-%H%M%S)" --serve "$@"
