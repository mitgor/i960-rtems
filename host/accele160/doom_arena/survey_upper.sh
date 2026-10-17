#!/usr/bin/env bash
# Read-only upper-DRAM inventory. Zero bytes do not confer ownership.
set -euo pipefail
[[ $(id -u) == 0 && $# == 2 ]] || { echo 'usage: sudo survey_upper.sh MMIO_SNAPSHOT OUT_DIR' >&2; exit 2; }
reader=$1 out=$2
dev=/sys/bus/pci/devices/0000:37:09.1
old=/sys/bus/pci/devices/0000:37:04.1
[[ -x $reader && ! -e $out ]] || exit 2
[[ $(<"$dev/vendor") == 0x1069 && $(<"$dev/device") == 0x0050 &&
   $(<"$dev/subsystem_vendor") == 0x1069 && $(<"$dev/subsystem_device") == 0x0054 ]] || exit 2
[[ $(basename "$(readlink -f "$dev/driver")") == myrsread ]] || exit 2
[[ $(</sys/module/myrsread/parameters/read_bdf) == 0000:37:09.1 ]] || exit 2
[[ ! -L $old/driver && ! -e /sys/module/dma_pin && ! -e /sys/module/admit_command ]] || exit 2
[[ $(<"$dev"/host*/scsi_host/host*/stock_descriptor) == 'state=0 status=0 residual=0' ]] || exit 2
exec 9>/run/lock/i960-loadrun.lock
flock -n 9
original=$(setpci -s 37:09.1 44.L)
[[ $original == c0000000 ]] || exit 2
mkdir -m 700 "$out"
restore() { setpci -s 37:09.1 44.L="$original"; [[ $(setpci -s 37:09.1 44.L) == "$original" ]]; }
trap restore EXIT
trap 'exit 130' INT TERM
cat /proc/sys/kernel/random/boot_id >"$out/boot-id.txt"
cat "$dev"/host*/scsi_host/host*/stock_descriptor >"$out/descriptor-before.txt"
for round in 0 1; do
  for base in c0384000 c0800000 c0810000 c0854000 c08b0000 c08e0000 c0900000 c0a00000 c0b00000 c0c00000 c0d00000 c0e00000 c0f00000 c0ffe000; do
    setpci -s 37:09.1 44.L="$base"
    [[ $(setpci -s 37:09.1 44.L) == "$base" ]] || exit 1
    timeout 5s "$reader" "$dev/resource0" 0x1000 4096 "$out/$base-$round.bin"
    restore
  done
  [[ $round == 0 ]] && sleep 2
done
cat "$dev"/host*/scsi_host/host*/stock_descriptor >"$out/descriptor-after.txt"
[[ $(<"$out/descriptor-after.txt") == 'state=0 status=0 residual=0' ]] || exit 1
sha256sum "$out"/*.bin >"$out/sha256.txt"
restore
trap - EXIT
