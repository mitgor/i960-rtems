#!/usr/bin/env bash
# Read only the proposed loader-cave page on the AcceleRAID 160.
set -euo pipefail
test "$(id -u)" = 0
test "${1:-}" != "" && test "${2:-}" != ""
page=${3:-c000e000}
# PIATVR is 8 KiB-aligned; BAR's upper 4 KiB maps base + 0x1000.
# c000e000 therefore reads the loader's c000f000..c000ffff page.
case "$page" in c000a000|c000c000|c000e000) ;; *) exit 2;; esac
test "$(cat /sys/bus/pci/devices/0000:37:09.1/vendor)" = 0x1069
test "$(cat /sys/bus/pci/devices/0000:37:09.1/device)" = 0x0050
test "$(basename "$(readlink -f /sys/bus/pci/devices/0000:37:09.1/driver)")" = myrsread
test ! -e /sys/bus/pci/devices/0000:37:04.1/driver
exec 9>/run/lock/i960-loadrun.lock
flock -n 9
before=$(setpci -s 37:09.1 44.L)
test "$before" = c0000000
restore() { setpci -s 37:09.1 44.L="$before"; }
trap restore EXIT
setpci -s 37:09.1 44.L="$page"
test "$(setpci -s 37:09.1 44.L)" = "$page"
"$1" /sys/bus/pci/devices/0000:37:09.1/resource0 0x1000 4096 "$2"
restore
trap - EXIT
test "$(setpci -s 37:09.1 44.L)" = "$before"
sha256sum "$2"
