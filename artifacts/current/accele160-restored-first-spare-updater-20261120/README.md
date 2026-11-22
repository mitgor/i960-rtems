# Restored first spare in Slot 5: offline native updater candidate

The HP Z400 booted Linux on 2026-11-20 with the restored first spare as its sole
AcceleRAID card at `0000:37:09.1`. The other AcceleRAID slot was empty. The
stock `myrsread` driver attached, and two independent guarded `READIMAGE`
captures in the same boot returned identical 1 MiB data. Both have SHA-256
`fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816`,
matching the archived stock image for this first spare. See
`../accele160-restored-return-20261120/` for the physical read receipts.

`native-updater-first-spare-slot5.bin` is a **proposed** card-specific image,
SHA-256 `17804234a6198963753674e4c6b074777a95c7fbab717e5d914d5376ad54dc29`.
It preserves the stock reset block, x86 option ROM, diagnostics, and card
descriptor. The mutable i960 firmware blocks at 0x40000–0xbffff contain the
native boot and UPD1 service. `pack-receipt.json` and `update-manifest.json`
record the exact stock and target identities.

Offline checks passed:

- `qemu-post-gate.json`: the modeled PCI configuration retry was released and
  SeaBIOS reached a boot sector.
- `interpreter-updater-gate.json`: the i960 interpreter accepted all 256 UPD1
  chunks, sealed, and aborted; it rejected out-of-order, bad-hash, and
  protected-region writes.
- `s3-model-replay.json`: the Intel S3 command model reconstructed the exact
  proposed image from the stock image.
- The exact stock/candidate pair is pinned in `preflight.py`; its test accepts
  the two current read receipts and rejects reads from the previous Slot 5 card.

On 2026-11-20, the candidate staged in controller RAM and an independent full
READIMAGE matched it byte for byte. The same-boot flash preflight passed, then
one `FLASHIMAGE` command completed in 34.9 seconds with status 0 and residual 0.
The card remained visible in PCI configuration afterward. See `remote-evidence/`
for stage, readback, and flash receipts. The HP Z400 was shut down for a cold
boot test. It beeped and booted Linux on boot ID
`a56bddf8-2ee3-4615-ba27-cd9f84f2cdfa`. The sole Slot 5 card enumerated.
The bounded PCI0 and status reports in `remote-evidence/` show PCI
configuration retry released, option ROM hidden, stage two started, and RTEMS
`PASS`; PCI identity stayed responsive for 45 seconds after each report read.
The offline `check_native_boot.py` review passed. The UPD1 implementation is
present in the flashed image, but its control interface and RAM staging have
not yet been exercised on physical hardware. A successful FLASHIMAGE and boot
do not prove an in-system update cycle.

An external programmer and the archived stock image remain the recovery path
if a later update or boot fails.
