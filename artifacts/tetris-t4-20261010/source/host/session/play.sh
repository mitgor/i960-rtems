#!/bin/sh
# Installed alongside the terminal client and the other host Python modules.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sudo -n python3 "$HERE/terminal.py" \
  --payload "$HERE/tetris_payload.bin" --module "$HERE/dac960session.ko" \
  --output "$HERE/sessions/$(date +%Y%m%d-%H%M%S)" "$@"
