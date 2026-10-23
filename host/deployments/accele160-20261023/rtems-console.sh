#!/usr/bin/env bash
set -euo pipefail
exec sudo env I960_RUNTIME_SOCKET=/run/i960-combined.sock python3 /home/mit/i960-packet-dma-20261019/service.py "$@"
