# Preserved boot-block recovery service — 2026-10-10

Latest: [STAGING-POINTER-VERIFIED.md](../loader/STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

Latest: [SSH recovery-entry investigation](SSH-RECOVERY-ENTRY.md) and [serial preparation](SERIAL-RECOVERY-SETUP.md). Physical access is available; serial comes later. Read-only SSH preflight passed; RAM-offset lead remains unproven and no recovery transition was attempted.

**A recovery service exists in the exact installed boot block.** It is copied into
DRAM and can expose PCI image-transfer/programming commands without main firmware.
This is static code evidence, not a recovery test. The card remains in normal
firmware; no recovery entry, PCI write, upload, reset or flash occurred. The user
requested continuing over SSH, without physical serial access.

## Failure path and entry

The installed 16 KiB boot block contains a 0x2A00-byte region at FEFFD600
(full-ROM offset 7D600). FEFFCAA8 copies it to C0010000, and FEFFCD90 returns
that address to the startup's final branch. Everything copied is inside the
preserved boot block, including its trailing data; the extracted length is not
an assertion that every byte is executable.

Normal boot at FEFFCC30 takes this fallback after a bad XLYM descriptor signature,
missing type-2 component, metadata word-sum mismatch, or copied-bootstrap word-sum
mismatch. The string `!ZipCkS` labels the last check, but the checked range is the
bootstrap range described by metadata, not a checksum of all decompressed code.
The recovery routine constructs fault-handler state before copying/entering the
monitor. Do not jump to its RAM entry without that setup.

There is also a serial trigger in FEFFC568–FEFFC60C: startup drains the receive
queue, transmits byte 53 (`S`), then samples received input after initialization.
Received 53 selects mode argument 1; received 21 (`!`) selects argument 2.
Mode 1 enters the fallback service and prints `Remove Serial Port Jumper`.
Mode 2 attempts the type-5 manufacturing component and falls back if its checks
fail. This is evidence of a serial-loopback/manufacturing mechanism; pinout,
voltage levels, exact timing and physical activation are not established here.
It is not a documented SSH-triggerable command.

**A valid custom loader that hangs does not fail these boot checks.** There is no
observed automatic rollback after the main entry receives control. Preserving the
boot block helps with damaged firmware, but does not by itself make every failed
custom build recoverable remotely.

## Recovery monitor behavior

The relocated disassembly is
[recovery-monitor.dis](../../artifacts/boot-recovery-20261010/recovery-monitor.dis).
All addresses in the following table are RAM addresses after the copy.

| Location | Observed behavior |
|---|---|
| C0010118 | Writes PCI vendor 1069 and device **0011**, BAR limit FFFFE000, translation C0000000 |
| C0010178 | Sets ROM limit FFFFF800 and translation FEFFC000 for the boot-block BIOS |
| C001003C | Writes EBCR 8 before the full flash-to-staging copy |
| C0010044 | Copies 512 KiB from FEF80000 into staging at C0140000 |
| C0010060 | Checks staging descriptor; constructs default entries if its signature is bad |
| C00104C0 | Polls messaging-unit state and services mailbox/serial activity |
| C0010540 | Recognizes opcodes 20, 21 and 2B; other opcodes return 0104 |
| C00105A0 / 05E0 | Transfers between host DMA and staging with supplied offset/count |
| C0010910 | Dispatches 2B subcommands 1 (program), 2 (descriptor read), 3 (descriptor upload) |
| C0010620 | Erases/programs the same lower 496 KiB map recovered from normal firmware |
| C0010774 | After successful programming, services serial activity in a loop; does not resume ordinary mailbox polling |

The recovery programming routine has no boot-block rewrite branch in the inspected
path. Its six requested erase ranges stop at FEFFC000. Thus the resident recovery
code is not in that requested erase map. This does not replace chip identification
or a restoration test.

The monitor uses mailbox memory C0001000 and completion fields C0001018/101A;
MU doorbell registers are 1320/132C. This supports the same PG-style host aperture
layout, but host enumeration and DMA remain untested in this mode. Existing dump
software requires device 0010 and Enquiry2; recovery does not implement Enquiry2.
It must not simply be run unchanged against 0011. The inspected transfer handlers
also have no obvious offset/count bounds checks, so a future read-only harness
must enforce the 512 KiB staging limit itself.

Because staging is copied after PCI configuration retry is released, enumeration
alone does not prove the copy has completed. If the flash descriptor is bad, the
monitor modifies its staging copy to supply defaults; that copy is then not a
byte-exact physical-flash backup.

## Vendor package checks traced

The decoded EXE is identical in the 29 and 39 packages. Corrected public symbols
and [evidence excerpts](../../artifacts/boot-recovery-20261010/evidence.dis) establish:

- `_GetImageHeader` (file 1800) reads the 512-byte header, checks MIMGMYLX and accepts
  type values 1 through 15. It returns declared length plus the caller's file
  offset. This routine is not a complete payload verifier.
- `_store_image2` calls `_CheckAdpDevId` at 66EE with controller type, MIMG word +58,
  and image type. The comparison masks the controller with FE; a zero MIMG adapter
  word defaults to 10. Our package has word 0010, compatible with both 0010 and
  0011 under this comparison. This alone does not verify PCI discovery.
- For our type-2 component, the path advances past the 512-byte header and reads
  declared length minus 512, then rejects a short read (695B–6A1F). Our declared
  38200 yields payload 38000, matching the installed descriptor's type-2 length.
- `_StoreRoadRunnerImage` scans the descriptor's 40-byte entries for the requested
  type at entry +8. Our stock type-2 entry is offset 30000, length 38000. It also
  edits/uploads descriptor fields; those mutations and full updater acceptance
  are not completely simulated by the package builder.

`loader/postinit/audit_recovery.py` performs these **partial** layout/adapter/length
checks offline, extracts the monitor from the pinned stock image, and emits
[audit.json](../../artifacts/boot-recovery-20261010/audit.json). It keeps
`vendor_acceptance_verified`, `hardware_validated` and `flash_ready` false.
The native test and 18 Python tests pass, including monitor preservation in the
candidate and rejection of malformed donors/packages.

Reproduction, using a new output directory:

```sh
python3 -B loader/postinit/audit_recovery.py \
  --stock artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --package artifacts/postinit-update-20261010/experimental-firmware.img \
  --out-dir /tmp/i960-recovery-audit
make -C loader/postinit test
```

The remote i960 objdump was used only to disassemble an extracted file:
`i960-coff-objdump -D -b binary -m i960 --adjust-vma=0xc0010000 recovery-monitor.bin`.
No vendor or extracted executable was run on the controller.

## Next SSH-only work

Recovery code availability is now established; deliberate non-destructive entry
from the running stock firmware is not. The next useful investigation is a stock
command/callback route into RAM execution or recovery that does not erase flash,
and verification of any side effects before using it. Do not corrupt a descriptor
or checksum merely to force the fallback. If no such route exists, an actual
recovery test will need a verified physical trigger or independent programmer.

A future recovery acceptance test starts with cold-boot enumeration as 1069:0011
and bounded descriptor/image reads only. Flashing remains gated on tested recovery,
complete staging preservation, and the loader DMA/watchdog/stack audit. The v2
loader and update package have not changed in this step.
