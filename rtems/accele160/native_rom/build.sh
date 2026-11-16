#!/usr/bin/env bash
# Cross-build only. This script never contacts the card or programs flash.
set -euo pipefail
if [[ $# != 3 ]]; then
  echo "usage: $0 RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR" >&2
  exit 2
fi
rtems_build=$(cd "$1" && pwd)
tools_bin=$(cd "$2" && pwd)
src=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$3"
out=$(cd "$3" && pwd)
app_flags=()
start_flags=()
mailbox_objects=()
if [[ ${ACCELE160_EARLY_ENTRY_MARKER:-0} == 1 ]]; then
  start_flags+=(-DACCELE160_EARLY_ENTRY_MARKER)
fi
if [[ ${ACCELE160_OBSERVE_HOST_EVENTS:-0} == 1 ]]; then
  app_flags+=(-DACCELE160_OBSERVE_HOST_EVENTS)
fi
if [[ ${ACCELE160_READ_ROM_MAILBOX:-0} == 1 ]]; then
  if [[ ${ACCELE160_OBSERVE_HOST_EVENTS:-0} != 1 ]]; then
    echo "ACCELE160_READ_ROM_MAILBOX requires ACCELE160_OBSERVE_HOST_EVENTS" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_READ_ROM_MAILBOX)
  "$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
    -c "$src/host_mailbox.c" -o "$out/host_mailbox.o"
  mailbox_objects+=("$out/host_mailbox.o")
fi
if [[ ${ACCELE160_COMPOSE_CTLR_INFO:-0} == 1 ]]; then
  if [[ ${ACCELE160_READ_ROM_MAILBOX:-0} != 1 ]]; then
    echo "ACCELE160_COMPOSE_CTLR_INFO requires ACCELE160_READ_ROM_MAILBOX" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_COMPOSE_CTLR_INFO)
  "$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
    -c "$src/controller_info.c" -o "$out/controller_info.o"
  mailbox_objects+=("$out/controller_info.o")
fi
if [[ ${ACCELE160_EMULATOR_DMA1_REPLY:-0} == 1 ]]; then
  if [[ ${ACCELE160_COMPOSE_CTLR_INFO:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_DMA1_REPLY requires ACCELE160_COMPOSE_CTLR_INFO" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_DMA1_REPLY)
fi
if [[ ${ACCELE160_EMULATOR_IOCTL11:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_DMA1_REPLY:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_IOCTL11 requires ACCELE160_EMULATOR_DMA1_REPLY" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_IOCTL11)
fi
if [[ ${ACCELE160_EMULATOR_IOCTL15:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_IOCTL11:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_IOCTL15 requires ACCELE160_EMULATOR_IOCTL11" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_IOCTL15)
fi
if [[ ${ACCELE160_EMULATOR_IOCTLD0:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_IOCTL15:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_IOCTLD0 requires ACCELE160_EMULATOR_IOCTL15" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_IOCTLD0)
fi
if [[ ${ACCELE160_EMULATOR_IOCTL2D:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_IOCTLD0:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_IOCTL2D requires ACCELE160_EMULATOR_IOCTLD0" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_IOCTL2D)
fi
if [[ ${ACCELE160_EMULATOR_SET_MBOX:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_IOCTL2D:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_SET_MBOX requires ACCELE160_EMULATOR_IOCTL2D" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_SET_MBOX)
fi
if [[ ${ACCELE160_EMULATOR_RING_OBSERVER:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_SET_MBOX:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_OBSERVER requires ACCELE160_EMULATOR_SET_MBOX" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_OBSERVER)
fi
if [[ ${ACCELE160_EMULATOR_RING_REPLY:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_OBSERVER:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_REPLY requires ACCELE160_EMULATOR_RING_OBSERVER" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_REPLY)
fi
if [[ ${ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_REPLY:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER requires ACCELE160_EMULATOR_RING_REPLY" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER)
fi
if [[ ${ACCELE160_EMULATOR_RING_HEALTH_REPLY:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_HEALTH_REPLY requires ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_HEALTH_REPLY)
fi
if [[ ${ACCELE160_EMULATOR_RING_PDEV_REPLY:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_HEALTH_REPLY:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_PDEV_REPLY requires ACCELE160_EMULATOR_RING_HEALTH_REPLY" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_PDEV_REPLY)
fi
if [[ ${ACCELE160_EMULATOR_RING_NEXT_OBSERVER:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_PDEV_REPLY:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_NEXT_OBSERVER requires ACCELE160_EMULATOR_RING_PDEV_REPLY" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_NEXT_OBSERVER)
fi
if [[ ${ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY:-0} == 1 ]]; then
  if [[ ${ACCELE160_EMULATOR_RING_NEXT_OBSERVER:-0} != 1 ]]; then
    echo "ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY requires ACCELE160_EMULATOR_RING_NEXT_OBSERVER" >&2
    exit 2
  fi
  app_flags+=(-DACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY)
fi
# Opt-in: program the stock host PCI identity and clear the 80303
# Configuration Cycle Retry bit (EBCR 0x1040 bit 2) at stage-two entry.
# Without it the existing stage-two bytes are unchanged.
stage2_flags=()
stage2_objects=()
if [[ ${ACCELE160_PCI_RELEASE:-0} == 1 ]]; then
  options=0
  if [[ ${ACCELE160_PCI_HIDE_OPTION_ROM:-0} == 1 ]]; then options=1; fi
  stage2_flags+=(-DACCELE160_PCI_RELEASE "-DACCELE160_PCI_RELEASE_OPTIONS=${options}u")
  "$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
    -c "$src/pci_release.c" -o "$out/pci_release.o"
  stage2_objects+=("$out/pci_release.o")
elif [[ ${ACCELE160_PCI_HIDE_OPTION_ROM:-0} == 1 ]]; then
  echo "ACCELE160_PCI_HIDE_OPTION_ROM requires ACCELE160_PCI_RELEASE" >&2
  exit 2
fi
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  "${stage2_flags[@]}" -c "$src/stage2.c" -o "$out/stage2.o"
"$tools_bin/i960-coff-gcc" -mrp -c "$src/stage2_start.S" -o "$out/stage2_start.o"
"$tools_bin/i960-elf-ld" -T "$src/stage2.ld" -Map "$out/stage2.map" \
  -o "$out/stage2.elf" "$out/stage2_start.o" "$out/stage2.o" \
  "${stage2_objects[@]}"
"$tools_bin/i960-elf-objcopy" -O binary "$out/stage2.elf" "$out/stage2.bin"
"$tools_bin/i960-elf-nm" -n "$out/stage2.elf" > "$out/stage2.symbols"
"$tools_bin/i960-coff-gcc" -mrp "${start_flags[@]}" -c "$src/start.S" -o "$out/start.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -D__rtems__ -DUSE_INLINES "${app_flags[@]}" -I"$rtems_build/include" \
  -I"$(dirname "$rtems_build")/newlib-1.11.0/newlib/libc/include" \
  -c "$src/app.c" -o "$out/app.o"
"$tools_bin/i960-coff-gcc" -mrp -Os -fno-builtin -ffreestanding \
  -c "$src/host_startup.c" -o "$out/host_startup.o"
"$tools_bin/i960-elf-ld" -T "$src/link.ld" -Map "$out/rtems.map" \
  -o "$out/rtems.elf" "$out/start.o" "$out/app.o" "$out/host_startup.o" \
  "${mailbox_objects[@]}" \
  "$rtems_build/context.o" "$rtems_build/libc.o" \
  "$rtems_build/librtems-bounded.a"
"$tools_bin/i960-elf-objcopy" -O binary "$out/rtems.elf" "$out/rtems.bin"
"$tools_bin/i960-elf-nm" -n "$out/rtems.elf" > "$out/rtems.symbols"
python3 - "$out" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
def symbols(name):
    return {line.split()[-1]: int(line.split()[0], 16)
            for line in (p / name).read_text().splitlines()
            if len(line.split()) == 3 and line.split()[0][0] in '0123456789abcdef'}
s, r = symbols('stage2.symbols'), symbols('rtems.symbols')
assert s['_stage2_entry'] == 0xc000a000, hex(s['_stage2_entry'])
assert r['_start'] == 0xc0010000, hex(r['_start'])
assert len((p/'stage2.bin').read_bytes()) <= 0x6000
assert len((p/'rtems.bin').read_bytes()) <= 0x70000
assert len((p/'rtems.bin').read_bytes()) % 4 == 0
PY
sha256sum "$out/stage2.bin" "$out/rtems.bin"
