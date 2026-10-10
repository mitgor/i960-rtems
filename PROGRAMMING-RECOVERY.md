# Programming-path audit and offline update package — 2026-10-10

Latest (2026-10-10): [programming preflight and live CPU verification](PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


Latest: [BOOT-RECOVERY.md](BOOT-RECOVERY.md) establishes an embedded recovery monitor (PCI 1069:0011) and partial vendor validation. Entry/restoration remain untested; continue over SSH without forcing a flash fault.

The v2 loader can be represented as a firmware-only MIMG component, but **a
firmware-only update does not imply a firmware-only erase**. The matching firmware
programming routine erases the lower 496 KiB before rewriting it from staging.
No programming command, staging upload, reset, or remote hardware access was
performed during this step. Recovery and live custom execution remain unverified.

## What the matching firmware actually does

These findings come from the archived 4.07-0-29 decompressed program and bootstrap,
not from generic DAC960 opcode names. The vendor EXE in both Fujitsu packages has
SHA-256 `1be1c11f5e030be80cd55b5c9215734f472daf4ee651abd1da57284e4888c552`.
Relevant disassembly is preserved in
[programming-evidence.dis](artifacts/postinit-update-20261010/programming-evidence.dis).

The 512 KiB bootstrap route installs callback +EC = C004CF80 and +E8 = C004D6D0.
In the existing linear bootstrap disassembly these stores appear at `FEFCB7E4`
and `FEFCB7E8`; their actual copied
runtime addresses are C000C7E4 and C000C7E8.

- Opcode 22 schedules C004CD50, which calls +E8. C004D6D0 obtains/frees staging,
  clears its pointer, and returns status 0104. It is not this board's usable
  programming entry and is not a harmless capability probe.
- Opcode 2B/subcommand 1 schedules C004CDA0, which calls +EC after its scheduler
  preconditions. C004CF80 requires a staging buffer, returning 0105 if absent.
- Vendor `_ProgramRoadRunnerImage` at EXE offset 58F7 reads the descriptor with
  2B/2, increments a field, writes it with 2B/3, then submits 2B/1. Its argument
  becomes mailbox byte 3, which controls the additional boot-block operation.
- `_StoreRoadRunnerImage` uploads component bytes with 21 and also edits/uploads
  descriptor metadata. Thus simply placing our component over a saved full ROM
  does not simulate every vendor updater side effect.

C004CF80 calls erase helper C0050690 for these regions, then program helper
C00507B0 with successive portions of the full staging image:

| Flash offset | Length | End, exclusive | Selection |
|---|---|---|---|
| 00000 | 20000 | 20000 | Unconditional |
| 20000 | 20000 | 40000 | Unconditional |
| 40000 | 20000 | 60000 | Unconditional |
| 60000 | 18000 | 78000 | Unconditional |
| 78000 | 02000 | 7A000 | Unconditional |
| 7A000 | 02000 | 7C000 | Unconditional |
| 7C000 | 04000 | 80000 | Only when mailbox byte 3 is nonzero |

Addresses and sizes are hexadecimal. This is the routine's requested map, not
an independently measured physical chip identification. The erase helper writes
20/D0, polls status bit 7, and checks the requested range for FF. The program helper
writes bytes using command 40 and polls status. Neither inspected polling loop has
an obvious timeout; the program helper does not perform a full bytewise readback.
All six lower-region erase calls precede programming. A failed write can therefore
leave BIOS, firmware, utilities and descriptor unavailable even when the boot block
is preserved. Machine-readable ranges are in
[programming-map.json](artifacts/postinit-update-20261010/programming-map.json).

## Offline package produced

[experimental-firmware.img](artifacts/postinit-update-20261010/experimental-firmware.img)
is **229,898 bytes**, using the exact 512-byte header and 10-byte trailer from
Fujitsu's matching firmware component. The replacement payload is the v2 full-ROM
slice [30000,68000). Its SHA-256 is
`e4dc6ead76e7febc4e7c99ecf43bc2b01b76bbd08e3ce2cff076999f94140579`.
The package still advertises the original vendor version; its experimental name
and accompanying manifest distinguish it from stock.

`loader/postinit/package_update.py` requires the pinned stock ROM, pinned vendor
container and verified decompressed reference. It rebuilds the candidate using
our current builder, rejects mismatches, and verifies that replacing only the
firmware slice reconstructs the full v2 candidate exactly. It never invokes a
flasher. The manifest keeps `flash_ready`, `hardware_validated`, and
`vendor_acceptance_verified` false. This establishes layout consistency, not
complete vendor validation, flash geometry, or an accepted update transaction.

Reproduce into a new, nonexistent output path from the repository root:

```sh
python3 -B loader/postinit/package_update.py \
  --stock artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --candidate artifacts/postinit-preflight-20261010/experimental-full-rom.bin \
  --code artifacts/postinit-preflight-20261010/loader.bin \
  --unpacked artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin \
  --vendor artifacts/vendor-fujitsu/4.07-0-29/Fgj40729.img.decoded \
  --out /tmp/experimental-firmware.img
make -C loader/postinit test
```

The native dispatcher test and 14 Python tests pass. New tests check reconstruction,
header/trailer preservation, corrupted donors, truncated inputs and mutations in
both allowed component and preserved full-ROM regions.

## Recovery assessment and next work

The stock boot block remains byte-for-byte present in our candidate and the
programming callback can omit its erase. Neither fact establishes a working
recovery interface when main firmware or its descriptor is missing. BOOT-RECOVERY.md now identifies the embedded host command handler and serial
trigger in static code. Physical activation and a restoration test remain unverified.
Likewise, a healthy stock firmware can accept its usual update protocol, but our
resident loader implements a different mailbox protocol: the vendor DOS updater
cannot be assumed to restore stock after a successful custom boot. A separate
RAM-resident restore program would need development and validation.

The boot-block failure path and partial component checks are now traced in
BOOT-RECOVERY.md. Next is finding a non-destructive SSH-accessible entry, while
completing the vendor descriptor mutation and discovery analysis. A future programming procedure must account for the *entire* erased staging
range, not just our changed 666 bytes. Verify actual flash after completion through
a fresh source; an existing staging read is not programming verification.

Independent recovery remains unresolved under REFLASH.md. This audit provides no
basis to relax that requirement. The downstream SCSI bus-master, external watchdog,
inherited stack and payload-window checks listed in LIVE-TEST-PREFLIGHT.md also
remain open. No flash command is provided as a validated live procedure.
