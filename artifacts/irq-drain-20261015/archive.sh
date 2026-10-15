#!/bin/bash
set -euo pipefail
cd /home/mit/i960-irq-drain-20261015
mode=$1
if [ "$mode" = masked ]; then r=project; b=build; else case "$mode" in fixed|stress-masked|stress-fixed) ;; *) exit 1;; esac; r=project-$mode; b=build-$mode; fi
# Run only after the bounded runner finishes and replay succeeds.
tar --exclude=__pycache__ -czf "$mode-candidate.tar.gz" "$r" "$b/residentnet" "$b/residentnet-module" "$b/admission" "$b/packed" "$b/platform-cross" "$b/platform-host" "$b/play-build.json"
tar -czf "$mode-card.tar.gz" "live-$mode" "live-$mode.log"
sha256sum "$mode-candidate.tar.gz" > "$mode-candidate.tar.gz.sha256"
sha256sum "$mode-card.tar.gz" > "$mode-card.tar.gz.sha256"
