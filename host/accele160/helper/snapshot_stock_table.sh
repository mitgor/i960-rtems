#!/usr/bin/env bash
# Guarded, read-only AcceleRAID 160 stock table snapshot. Requires root.
# Only writes PIATVR to select the upper BAR aperture, then restores it.
set -euo pipefail

if (( $# != 2 )); then
  echo "usage: $0 MMIO_SNAPSHOT_BINARY OUTPUT_DIRECTORY" >&2
  exit 2
fi
snapshot=$1
out=$2
bdf=0000:37:09.1
dev=/sys/bus/pci/devices/$bdf
resource=$dev/resource0
original=
restored=0

[[ $(id -u) == 0 ]] || { echo 'root required' >&2; exit 2; }
[[ -x $snapshot && -d $dev && -e $resource ]] || { echo 'missing device or reader' >&2; exit 2; }
[[ $(< "$dev/vendor") == 0x1069 && $(< "$dev/device") == 0x0050 ]] || {
  echo 'unexpected PCI identity' >&2; exit 2;
}
[[ $(< "$dev/subsystem_vendor") == 0x1069 && $(< "$dev/subsystem_device") == 0x0054 ]] || {
  echo 'unexpected subsystem identity' >&2; exit 2;
}
[[ ! -L $dev/driver ]] || { echo 'new card has a driver; aborting' >&2; exit 2; }
[[ ! -L /sys/bus/pci/devices/0000:37:04.1/driver ]] || {
  echo 'old card has a driver; aborting' >&2; exit 2;
}
original=$(setpci -s 37:09.1 44.L)
[[ $original == c0000000 ]] || { echo "unexpected PIATVR=$original" >&2; exit 2; }
[[ $(setpci -s 37:09.1 COMMAND) == 0002 ]] || {
  echo 'unexpected PCI command register' >&2; exit 2;
}
[[ ! -e $out ]] || { echo 'output directory already exists' >&2; exit 2; }
mkdir -m 700 "$out"

restore() {
  if [[ -n $original && $restored == 0 ]]; then
    setpci -s 37:09.1 44.L="$original"
    if [[ $(setpci -s 37:09.1 44.L) != "$original" ]]; then
      echo 'FATAL: PIATVR restore readback failed' >&2
      return 1
    fi
    restored=1
  fi
}
trap restore EXIT
trap 'exit 130' INT TERM

"$snapshot" "$resource" 0x1000 4096 "$out/default-before.bin"
setpci -s 37:09.1 44.L=c0023000
[[ $(setpci -s 37:09.1 44.L) == c0023000 ]] || {
  echo 'PIATVR remap readback failed' >&2; exit 1;
}
"$snapshot" "$resource" 0x1000 4096 "$out/table-page.bin"
restore
"$snapshot" "$resource" 0x1000 4096 "$out/default-after.bin"
cmp "$out/default-before.bin" "$out/default-after.bin"
[[ $(od -An -tx4 -j 1276 -N 4 "$out/table-page.bin" | tr -d ' ') == c0023790 ]] || {
  echo 'live stock 0x8f table word did not match stock image' >&2; exit 1;
}
if [[ -n ${SUDO_USER:-} ]]; then
  chown "$SUDO_USER" "$out" "$out"/*.bin
fi
sha256sum "$out"/*.bin
echo 'PIATVR=c0000000 stock_0x8f=c0023790 old_card=untouched'
