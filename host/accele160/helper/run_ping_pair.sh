#!/usr/bin/env bash
# Positive and one-byte-bad signature controls on the programmed new card.
set -euo pipefail
test "$(id -u)" = 0
test "${1:-}" != "" && test "${2:-}" != ""
test "$(cat /sys/bus/pci/devices/0000:37:09.1/vendor)" = 0x1069
test "$(cat /sys/bus/pci/devices/0000:37:09.1/device)" = 0x0050
test "$(basename "$(readlink /sys/bus/pci/devices/0000:37:09.1/driver)")" = myrsread
test ! -e /sys/bus/pci/devices/0000:37:04.1/driver
exec 9>/run/lock/i960-loadrun.lock
flock -n 9
module=$1
out=$2
test ! -e "$out"
mkdir -m 700 "$out"
for bad in 0 1; do
    test ! -e /sys/kernel/debug/accele-pingprobe
    insmod "$module" bdf=0000:37:09.1 bad_signature="$bad"
    printf 'ping\n' >/sys/kernel/debug/accele-pingprobe/start
    for ((i=0;i<100;i++)); do
        state=$(cat /sys/kernel/debug/accele-pingprobe/status)
        [[ $state == started=1\ done=1* ]] && break
        sleep .05
    done
    printf '%s\n' "$state" >"$out/ping-$bad.txt"
    [[ $state == started=1\ done=1* ]] || {
        echo 'pending PING: retain module, do not unload' >&2; exit 1;
    }
    if (( bad == 0 )); then
        [[ $state == *'status=0 residual=0 bad_signature=0'* ]]
    else
        [[ $state == *'status=2 residual=0 bad_signature=1'* ]]
    fi
    printf 'release\n' >/sys/kernel/debug/accele-pingprobe/release
    rmmod ping_probe
done
cat "$out"/ping-*.txt
