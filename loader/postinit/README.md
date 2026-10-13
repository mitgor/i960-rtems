# Experimental loader after stock initialization

**Offline prototype only; not ready to flash.** This is a new DRAM-capable profile,
not a fix to the historical internal-RAM execution demo. No custom code from this
prototype has run on the card. See [POSTINIT-LOADER.md](../../docs/loader/POSTINIT-LOADER.md)
for evidence, exact hook and outstanding hardware gates.

The revision-2 832-byte loader inherits stock memory initialization and early PCI setup.
It polls the existing sequence protocol, accepts 64 KiB at C0120000–C012FFFF,
and invalidates instruction cache before GO. Arbitrary register commands are
disabled in this profile. The separate host `loadctl` must be compiled with
POSTINIT_PROFILE, as this Makefile does. The 20-byte `hello.bin` executes from
external DRAM, writes BEEF00EE to OMR1, and parks.

## Offline reproduction

With the i960 toolchain in PATH, from this directory:

```
make
make test
python3 build_image.py \
  --stock ../../artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --code loader.bin \
  --unpacked ../../artifacts/private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin \
  --out /tmp/experimental-full-rom.bin
```

The output is a raw 512 KiB image, **not a vendor update container**. There is no
flash target. The builder refuses other donor hashes and existing output paths.
It preserves the original boot block, reset vector, BIOS, descriptor and compressed
program, changing only zero padding and two metadata words. Both code placement
and image validation are specific to the archived installed image.

The archived build is in `artifacts/postinit-preflight-20261010/`, including
ELFs, binaries, map, disassemblies, Linux host tool and full candidate image.
`loader-raw.dis` gives the full instruction stream; the old ELF disassembler
reports out-of-bounds at some local symbols in `loader.dis`. No undefined loader
symbols were reported by the cross `nm -u` check.

## Intended hardware test, after the gates are resolved

The driverless card must already run this loader before using its host protocol.
A stock RAID firmware card must not be probed with these commands. Expected flow:
status/READY → ping → upload hello to C0120000 with readback → GO → status showing
BEEF00EE in OMR1. GO acknowledgement alone is not execution proof.

The current window is a candidate exclusive-memory allocation, not a coexistence
API for stock RAID. The firmware stops at the hook; it cannot continue after
payload upload. No return-to-stock or watchdog servicing is implemented. In
particular, do not treat the unchanged option ROM or preserved boot block as a
proven recovery mechanism after a bad flash.

## Read-only live inventory

`sudo python3 preflight.py --bdf 0000:37:09.1` reads sysfs configuration only.
The live result and current guard design are in [LIVE-TEST-PREFLIGHT.md](../../docs/loader/LIVE-TEST-PREFLIGHT.md).
A passing inventory does not permit flashing. V2 hooks before EBCR retry release,
suppresses ROM exposure and reports 60EF instead of READY if any DMA channel is active.

## Offline update packaging

See [PROGRAMMING-RECOVERY.md](../../docs/firmware/PROGRAMMING-RECOVERY.md) for `package_update.py`, the archived experimental MIMG, and the broader erase map. Packaging is not a live flash procedure; recovery remains unverified.
