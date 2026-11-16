#!/bin/sh
# Regenerate every file of this experiment from source. Offline: no card, no
# PCI device, no flash programming. Run from the repository root:
#
#   sh artifacts/current/accele160-pci-release-20261117/reproduce.sh OUT_DIR
#
# OUT_DIR must not already contain the generated files. Inputs that are not
# in this branch are found through environment variables:
#   TOOLCHAIN_CACHE  directory holding the archived i960 toolchain as "i960"
#                    and the bounded RTEMS build as "i960-rtems-20261115"
#                    (see artifacts/current/accele160-offline-build-20261115)
#   BUILD_IMAGE      linux/amd64 container image with bash and python3
#   QEMU, BIOS       optional: QEMU 6.2.0 built with this branch's accele160.c
#                    and the patched SeaBIOS; enables the host-side stall run
#   FIRST_SPARE_STOCK optional: first spare's own stock read, for its image
# The older gates need saved artifacts from the main checkout; link them
# first with link-main-checkout-artifacts.sh.
set -eu
out=$1
mkdir -p "$out"
out=$(cd "$out" && pwd)
root=$(pwd)
cache=${TOOLCHAIN_CACHE:-$HOME/Library/Caches/i960-offline-20261115}
image=${BUILD_IMAGE:-accele160-offline-python:22.04}
emu=rtems/accele160/emulator
native=rtems/accele160/native_rom
stock=artifacts/current/accele160-second-spare-20261026/rawflash-0/data.bin
failed=artifacts/current/accele160-spare-rom-20261025/native-rom-spare-prototype.bin

echo "== 1. i960 interpreter"
sh $emu/build.sh
shasum -a 256 $emu/build/accele160-emu > "$out/emulator-sha256.txt"

echo "== 2. reference register traces (stock, image that froze the HP Z400)"
python3 $emu/pci_register_trace.py --image $stock --out "$out/stock-pci-reg-writes.json"
python3 $emu/pci_register_trace.py --image $failed --cycles 3000000 \
  --out "$out/failed-first-spare-pci-reg-writes.json"

echo "== 3. host unit tests"
# The whole native-ROM suite needs the older saved artifacts; without them
# only the release test runs.
pattern='test_pci_release.py'
if [ -e artifacts/current/accele160-second-spare-20261026/native-rom-second-spare.bin ]; then
  pattern='test_*.py'
fi
STOCK_PCI_TRACE="$out/stock-pci-reg-writes.json" \
  python3 -m unittest discover -s $native -p "$pattern" 2>&1 | tee "$out/unit-tests.txt"
( cd host/accele160/offline_return && python3 -m unittest test_collect ) 2>&1 | tee -a "$out/unit-tests.txt"

echo "== 4. cross-build (container, archived toolchain mounted read-only)"
mkdir -p "$out/build"
cat > "$out/build/build-all.sh" <<'INNER'
set -euo pipefail
passive="ACCELE160_EARLY_ENTRY_MARKER=1 ACCELE160_OBSERVE_HOST_EVENTS=1 ACCELE160_READ_ROM_MAILBOX=1"
service="$passive ACCELE160_COMPOSE_CTLR_INFO=1 ACCELE160_EMULATOR_DMA1_REPLY=1 ACCELE160_EMULATOR_IOCTL11=1 ACCELE160_EMULATOR_IOCTL15=1 ACCELE160_EMULATOR_IOCTLD0=1 ACCELE160_EMULATOR_IOCTL2D=1 ACCELE160_EMULATOR_SET_MBOX=1 ACCELE160_EMULATOR_RING_OBSERVER=1 ACCELE160_EMULATOR_RING_REPLY=1 ACCELE160_EMULATOR_RING_FOLLOWUP_OBSERVER=1 ACCELE160_EMULATOR_RING_HEALTH_REPLY=1 ACCELE160_EMULATOR_RING_PDEV_REPLY=1 ACCELE160_EMULATOR_RING_NEXT_OBSERVER=1 ACCELE160_EMULATOR_RING_REPEAT_INFO_REPLY=1"
build() { name=$1; shift; echo "== $name"; env "$@" bash /project/rtems/accele160/native_rom/build.sh /home/mit/i960-rtems-20261115/accele160 /home/mit/i960/tools/bin /out/$name; rm -f /out/$name/*.o /out/$name/*.elf; }
build control-passive $passive
build passive-release $passive ACCELE160_PCI_RELEASE=1 ACCELE160_PCI_HIDE_OPTION_ROM=1
build service-release $service ACCELE160_PCI_RELEASE=1
build service-release-hidden-rom $service ACCELE160_PCI_RELEASE=1 ACCELE160_PCI_HIDE_OPTION_ROM=1
INNER
docker run --rm --platform linux/amd64 -v "$root":/project:ro \
  -v "$cache/i960":/home/mit/i960:ro \
  -v "$cache/i960-rtems-20261115":/home/mit/i960-rtems-20261115:ro \
  -v "$out/build":/out "$image" bash /out/build-all.sh > "$out/build/build.log" 2>&1
grep -E '^==|  /out/' "$out/build/build.log"

echo "== 5. pack against the second spare's own stock read"
pack() { python3 $native/pack.py "$1" "$out/build/$2/stage2.bin" "$out/build/$2/rtems.bin" "$out/$3.bin" > "$out/$3.pack-receipt.json"; }
pack $stock control-passive control-passive-no-release-second-spare
pack $stock passive-release native-passive-pci-release-second-spare
pack $stock service-release native-service-pci-release-second-spare
pack $stock service-release-hidden-rom native-service-pci-release-hidden-rom-second-spare
if [ -n "${FIRST_SPARE_STOCK:-}" ]; then
  pack "$FIRST_SPARE_STOCK" passive-release native-passive-pci-release-first-spare
fi
( cd "$out" && shasum -a 256 *.bin ) | tee "$out/image-sha256.txt"

echo "== 6. offline configuration-retry gate"
python3 $emu/config_retry_gate.py --stock $stock \
  --candidate "$out/native-passive-pci-release-second-spare.bin" \
  --candidate "$out/native-service-pci-release-hidden-rom-second-spare.bin" \
  --candidate-keeps-rom "$out/native-service-pci-release-second-spare.bin" \
  --must-hang $failed \
  --must-hang "$out/control-passive-no-release-second-spare.bin" \
  --output "$out/config-retry-gate.json"
if [ -n "${FIRST_SPARE_STOCK:-}" ]; then
  python3 $emu/config_retry_gate.py --stock "$FIRST_SPARE_STOCK" \
    --candidate "$out/native-passive-pci-release-first-spare.bin" \
    --must-hang $failed --output "$out/config-retry-gate-first-spare.json"
fi
echo "-- negative control: non-releasing images offered as candidates must fail"
if python3 $emu/config_retry_gate.py --stock $stock --candidate $failed \
    --candidate "$out/control-passive-no-release-second-spare.bin" \
    --output "$out/config-retry-gate-negative.json"; then
  echo "negative control unexpectedly passed" >&2; exit 1
fi

if [ -n "${QEMU:-}" ] && [ -n "${BIOS:-}" ]; then
  echo "== 7. host-side stall reproduction in coupled QEMU"
  set -- --must-boot $stock \
    --must-boot "$out/native-passive-pci-release-second-spare.bin" \
    --must-boot "$out/native-service-pci-release-hidden-rom-second-spare.bin" \
    --must-boot "$out/native-service-pci-release-second-spare.bin" \
    --must-stall $failed \
    --must-stall "$out/control-passive-no-release-second-spare.bin"
  for old in artifacts/current/accele160-minimal-diagnostic-20261116/native-service-marker-second-spare.bin \
             artifacts/current/accele160-second-spare-20261026/native-rom-second-spare-no-x86-rom.bin; do
    if [ -e "$old" ]; then set -- "$@" --must-stall "$old"; fi
  done
  python3 $emu/qemu/test_config_retry_post.py --qemu "$QEMU" --bios "$BIOS" \
    ${QEMU_DATA:+--qemu-data "$QEMU_DATA"} "$@" --output "$out/config-retry-post.json"
else
  echo "== 7. skipped (set QEMU and BIOS for the coupled host-side run)"
fi

direct=artifacts/current/accele160-minimal-diagnostic-20261116/run_service_direct.sh
if [ -e "$direct" ]; then
  echo "== 8. existing gates re-run on the new service image (regression)"
  mkdir -p "$out/regression"
  for pair in "old-service:artifacts/current/accele160-minimal-diagnostic-20261116/native-service-marker-second-spare.bin" \
              "service-release:$out/native-service-pci-release-second-spare.bin" \
              "service-release-hidden-rom:$out/native-service-pci-release-hidden-rom-second-spare.bin"; do
    name=${pair%%:*}; img=${pair#*:}
    sh "$direct" "$img" "$out/regression/$name-direct.json" > "$out/regression/$name-direct.txt" 2>&1
    echo "$name: $(tail -1 "$out/regression/$name-direct.txt")"
  done
  python3 $emu/test_native_readiness_negative.py --emulator $emu/build/accele160-emu \
    --image "$out/native-service-pci-release-second-spare.bin" \
    --first-fixture artifacts/current/accele160-offline-build-20261115/first-controller-info-fixture.json \
    | tee "$out/regression/service-release-readiness-negative.txt"
  guest=artifacts/current/accele160-myrs-guest-20261116
  if [ -n "${QEMU:-}" ] && [ -n "${BIOS:-}" ] && [ -e "$guest/vmlinuz-6.1.0-55-amd64" ]; then
    coupled="$out/regression/service-release-coupled"
    mkdir -p "$coupled"
    python3 $emu/qemu/test_native_card.py --emulator $emu/build/accele160-emu \
      --image "$out/native-service-pci-release-second-spare.bin" --qemu "$QEMU" \
      --bios "$BIOS" --kernel "$guest/vmlinuz-6.1.0-55-amd64" \
      --initrd "$guest/initramfs-myrs.cpio.gz" --memory-mb 512 --seconds 65 \
      --health-dma1 --pdev-dma1 --mirror-followups --next-observe --next-mirror \
      --rom-output "$coupled/rom.json" --serial-output "$coupled/serial.log" \
      --emulator-output "$coupled/emu.log" --qemu-stderr-output "$coupled/qemu.log" \
      > "$coupled/run.txt" 2>&1
    tail -1 "$coupled/run.txt"
    echo "-- same guest harness, retry model on, host started cold (1000 i960 instructions)"
    for pair in "service-release-coupled-retry-model:$out/native-service-pci-release-second-spare.bin:pass" \
                "old-service-coupled-retry-model:artifacts/current/accele160-minimal-diagnostic-20261116/native-service-marker-second-spare.bin:stall"; do
      name=${pair%%:*}; rest=${pair#*:}; img=${rest%:*}; want=${rest##*:}
      coupled="$out/regression/$name"
      mkdir -p "$coupled"
      status=0
      python3 $emu/qemu/test_native_card.py --emulator $emu/build/accele160-emu \
        --image "$img" --qemu "$QEMU" --bios "$BIOS" \
        --kernel "$guest/vmlinuz-6.1.0-55-amd64" \
        --initrd "$guest/initramfs-myrs.cpio.gz" --memory-mb 512 --seconds 65 \
        --health-dma1 --pdev-dma1 --mirror-followups --next-observe --next-mirror \
        --model-config-retry --prerun-cycles 1000 \
        --rom-output "$coupled/rom.json" --serial-output "$coupled/serial.log" \
        --emulator-output "$coupled/emu.log" --qemu-stderr-output "$coupled/qemu.log" \
        > "$coupled/run.txt" 2>&1 || status=$?
      retry=$(grep -h "config-retry" "$coupled/qemu.log" | head -1)
      echo "$name: exit=$status $retry"
      case "$want:$status:$retry" in
        pass:0:*released*) ;;
        stall:[1-9]*:*STALL*) ;;
        *) echo "unexpected outcome for $name" >&2; exit 1 ;;
      esac
    done
  fi
else
  echo "== 8. skipped (older saved artifacts are not linked into this worktree)"
fi
echo "done: $out"
