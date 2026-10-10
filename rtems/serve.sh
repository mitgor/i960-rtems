#!/bin/sh
# Installed in the build directory by deploy.py. Foreground, Ctrl-C to restore.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sudo -n python3 "$base/project/rtems/transport/relay.py" \
  --payload "$base/net/kernel.bin" --module "$base/module/dac960rtems.ko" \
  --output "$base/sessions/$(date -u +%Y%m%d-%H%M%S)" --serve "$@"
