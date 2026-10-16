#!/usr/bin/env bash
# Bounded read-only samples of the AcceleRAID 160 local DRAM aperture.
# The observations characterize activity; they confer no RAM ownership.
set -euo pipefail
[[ $(id -u) == 0 && $# == 2 ]] || { echo 'usage: sudo survey_dram.sh MMIO_READER OUT_DIR' >&2; exit 2; }
reader=$1 out=$2
bdf=0000:37:09.1
dev=/sys/bus/pci/devices/$bdf
[[ -x $reader && ! -e $out ]] || exit 2
[[ $(< "$dev/vendor") == 0x1069 && $(< "$dev/device") == 0x0050 ]] || exit 2
[[ $(< "$dev/subsystem_vendor") == 0x1069 && $(< "$dev/subsystem_device") == 0x0054 ]] || exit 2
[[ $(basename "$(readlink -f "$dev/driver")") == myrsread ]] || exit 2
[[ ! -L /sys/bus/pci/devices/0000:37:04.1/driver ]] || exit 2
exec 9>/run/lock/i960-loadrun.lock
flock -n 9
original=$(setpci -s 37:09.1 44.L)
[[ $original == c0000000 ]] || exit 2
mkdir -m 700 "$out"
restore() { setpci -s 37:09.1 44.L="$original"; [[ $(setpci -s 37:09.1 44.L) == "$original" ]]; }
trap restore EXIT
trap 'exit 130' INT TERM
cat /proc/sys/kernel/random/boot_id >"$out/boot-id.txt"
for round in 0 1; do
  for base in c0010000 c0384000 c04ac000 c0500000 c0800000 c0c00000 c0f00000; do
    setpci -s 37:09.1 44.L="$base"
    [[ $(setpci -s 37:09.1 44.L) == "$base" ]] || exit 1
    timeout 5s "$reader" "$dev/resource0" 0x1000 4096 "$out/$base-$round.bin"
    restore
  done
  [[ $round == 0 ]] && sleep 2
done
sha256sum "$out"/*.bin >"$out/sha256.txt"
restore
trap - EXIT
