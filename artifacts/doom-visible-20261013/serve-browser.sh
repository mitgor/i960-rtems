#!/bin/bash
set -euo pipefail
cd /home/mit/i960-doom-visible-20261013
test -s live/browser/index.html
test -s live/browser/frames.json
# Only the static frame directory is exposed. This process never opens the card.
exec python3 -m http.server 8086 --bind 192.168.2.75 --directory "$PWD/live/browser"
