#!/bin/bash
set -euo pipefail
cd /home/mit/i960-point-side-20261016
name=$1
test -s "$name-system.json"
test -s "$name-frames.json"
tar -czf "$name-card.tar.gz" "live-$name" "live-$name.log" "$name-system.json" "$name-frames.json" "$name-wad.json" "$name-profile.json" "$name-drain-tamper.json" "$name-frame-tamper.json"
sha256sum "$name-card.tar.gz" > "$name-card.tar.gz.sha256"
