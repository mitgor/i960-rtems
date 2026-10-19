#!/usr/bin/env bash
set -euo pipefail
# The argument must name the frozen candidate's runtime source directory.
root=${1:?usage: start_link.sh RUNTIME_SOURCE_DIR [pio|dma]}
transport=${2:-pio}
case "$transport" in pio|dma) ;; *) exit 2;; esac
systemd-run --unit=i960-rtems-ip --collect \
 --setenv=I960_RUNTIME_SOCKET=/run/i960-combined.sock \
 --setenv=I960_REPLY_TRANSPORT="$transport" \
 /usr/bin/python3 "$root/relay.py" --name accele0 --seconds 0
for _ in $(seq 1 50); do [[ -d /sys/class/net/accele0 ]] && break; sleep .1; done
ip addr add 10.196.0.1/30 dev accele0
ip -6 addr add fd96:196:960::1/64 dev accele0
ip link set accele0 mtu 1500 up
python3 "$root/public_ipv6.py" apply --address 2a02:8106:40:9000::960
